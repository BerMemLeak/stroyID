"""Export-only registers; the original card's full lists are never rewritten."""
from copy import deepcopy
import html
import re

KINDS = [('materials', 'материалов', 'М', 'АОСР.Материалы'),
         ('evidence', 'подтверждающих документов', 'Д', 'АОСР.ПодтверждающиеДокументы'),
         ('attachments', 'приложений', 'П', 'АОСР.Приложения')]


def expand_registers(plan):
    plan = deepcopy(plan)
    for volume in plan['volumes']:
        documents = []
        for item in volume['documents']:
            documents.append(item)
            config = item.get('actRegister')
            if not config or item['kind'] not in ('word', 'html'):
                continue
            values = dict(config['values'])
            values.update(item.get('values', {}))
            references, registers = [], []
            for kind, label, suffix, tag in KINDS:
                settings = config.get('settings', {}).get(kind, {})
                if not settings.get('enabled'):
                    continue
                entries = list(config['entries'].get(kind, []))
                if kind == 'attachments':
                    entries += references
                if not entries:
                    raise ValueError(f"АОСР {config['number']}: пустой реестр {label}")
                number = settings.get('number') or config['number'] + '-' + suffix
                date = settings.get('date') or values.get('АОСР.Дата', '')
                if not date:
                    raise ValueError(f"АОСР {config['number']}: не указана дата реестра")
                title = 'Реестр ' + label
                reference = f'{title} № {number} от {date}'
                values[tag] = 'Согласно реестру ' + label + f' № {number} от {date}'
                if kind != 'attachments':
                    references.append(reference)
                reg_values = {**values, 'Документ.Наименование': title,
                              'Документ.Номер': number, 'Документ.Дата': date,
                              'Реестр.КоличествоПозиций': str(len(entries)),
                              'Реестр.Текст': '\n'.join(f'{i}. {t}' for i, t in enumerate(entries, 1)),
                              'Документ.Содержание': '\n'.join(entries)}
                reg = {'id': item['id'] + ':register:' + kind, 'type': title,
                       'name': f'{title} № {number} к АОСР № {config["number"]}',
                       'nd': f'№ {number} от {date}', 'kind': 'html',
                       'ownerActId': config['actId'], 'sourceRef': item.get('sourceRef', ''),
                       'values': reg_values,
                       'collections': {'Реестр': [{'Номер': i, 'Наименование': t, 'Тип': '',
                           'Номер_Дата': '', 'КоличествоСтраниц': '', 'Листы': ''}
                           for i, t in enumerate(entries, 1)]}}
                esc = lambda s: html.escape(str(s or ''))
                rows = ''.join(f'<tr><td>{i}</td><td>{esc(t)}</td></tr>' for i, t in enumerate(entries, 1))
                signatures = ''.join('<p>' + esc(role) + ': __________________ ' + esc(name) + '</p>'
                                     for role, name in config.get('signers', []) if name)
                reg['html'] = (f'<h2>{esc(title)} № {esc(number)}</h2>'
                    f'<p align="center">к АОСР № {esc(config["number"])} от {esc(values.get("АОСР.Дата"))}</p>'
                    f'<p>{esc(values.get("Объект.Наименование"))}</p><p>Дата реестра: {esc(date)}</p>'
                    '<table border="1" cellspacing="0" width="100%"><thead><tr><th width="7%">№</th>'
                    f'<th>Наименование</th></tr></thead><tbody>{rows}</tbody></table>{signatures}')
                if config.get('templateKey'):
                    reg.update(kind='word', templateKey=config['templateKey'])
                elif config.get('builtinTemplate'):
                    reg.update(kind='word', builtinTemplate='act-register')
                if kind == 'attachments' and item.get('attachmentPageRefs'):
                    reg['attachmentPageRefs'] = dict(item['attachmentPageRefs'])
                registers.append(reg)
            if references and not config.get('settings', {}).get('attachments', {}).get('enabled'):
                values['АОСР.Приложения'] = '\n'.join(filter(None, [values.get('АОСР.Приложения', ''), *references]))
            if registers:
                for _, _, _, tag in KINDS:
                    old = item.get('values', {}).get(tag, config['values'].get(tag, ''))
                    new = values.get(tag, '')
                    if old != new and item.get('html'):
                        replacement=html.escape(str(new)).replace('\n', '<br>')
                        pattern=r'(<div class="pl" data-act-tag="'+re.escape(tag)+r'">).*?(</div>)'
                        if re.search(pattern,item['html'],re.S):
                            item['html']=re.sub(pattern,lambda m:m[1]+replacement+m[2],item['html'],flags=re.S)
                        elif old:
                            item['html']=item['html'].replace(html.escape(str(old)).replace('\n','<br>'),replacement)
                if item['kind'] == 'word':
                    item['values'] = values
                if config.get('settings', {}).get('attachments', {}).get('enabled'):
                    item.pop('attachmentPageRefs', None)
                documents += registers
        volume['documents'] = documents
    return plan


class ActPageError(ValueError):
    def __init__(self, issues):
        self.details = issues
        super().__init__('АОСР должен занимать две страницы.\n' + '\n'.join(
            f"{x['number']}: {x['pages']} стр." for x in issues) +
            '\nВынесите перечни в реестры или исправьте текст / шаблон акта.')


def enforce_act_pages(volumes):
    import io
    from pypdf import PdfWriter, PdfReader
    issues = []
    for volume in volumes:
        for doc in volume['documents']:
            if doc.get('type') != 'АОСР':
                continue
            config = doc.get('actRegister', {})
            if doc['count'] > 2:
                suggested = [key for key, _, _, _ in KINDS if doc['kind'] in ('word','html')
                             and config.get('entries', {}).get(key)
                             and not config.get('settings', {}).get(key, {}).get('enabled')]
                issues.append({'kind': 'actOverflow', 'actId': config.get('actId', ''),
                    'number': config.get('number') or doc.get('nd') or doc['name'],
                    'pages': doc['count'], 'suggested': suggested, 'sourceRef': doc.get('sourceRef', '')})
            elif doc['count'] == 1:
                writer = PdfWriter(); writer.append(doc['reader'], pages=doc['selection'], import_outline=False)
                page = writer.pages[0]
                writer.add_blank_page(float(page.mediabox.width), float(page.mediabox.height))
                data = io.BytesIO(); writer.write(data); writer.close()
                doc.update(reader=PdfReader(io.BytesIO(data.getvalue())), selection=[0, 1], count=2)
    if issues:
        raise ActPageError(issues)
