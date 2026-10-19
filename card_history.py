"""Per-card revision UI, immutable attachment snapshots and replicated pruning.

The event graph remains the authority. Numbered folders are readable projections;
pruned graph nodes remain as small ancestry stubs, never as alternate live heads.
"""
import copy
import hashlib
import json
import re
import shutil
import uuid
from pathlib import Path
from folder_core import LABELS, atomic, digest, encode, safe, stamp, walk

ASSET_FIELDS = (('fileKey', 'fileHash'), ('photoKey', 'photoHash'),
                ('logoKey', 'logoHash'), ('signKey', 'signHash'))
HISTORY_DIR = 'История версий'


def supported(key):
    return key.split(':', 1)[0] in LABELS


def semantic(record):
    if record is None:
        return None
    return {k: v for k, v in record.items() if k != 'position'}


def differences(old, new, trail=''):
    """Stable field paths, including identified rows rather than positional rows."""
    if old == new:
        return []
    if isinstance(old, dict) and isinstance(new, dict):
        result = []
        for key in sorted(set(old) | set(new)):
            if key in ('fileHash', 'photoHash', 'logoHash', 'signHash'):
                continue
            result += differences(old.get(key), new.get(key), (trail + '.' if trail else '') + key)
        return result
    if isinstance(old, list) and isinstance(new, list) and all(isinstance(x, dict) and x.get('id') for x in old + new):
        a, b = ({x['id']: x for x in values} for values in (old, new))
        return differences(a, b, trail)
    return [{'field': trail, 'before': old, 'after': new}]


class CardHistory:
    def _generation(self, ident, seen=None):
        cache = self.__dict__.setdefault('_history_generations', {})
        if ident in cache:
            return cache[ident]
        event = self.events.get(ident, {})
        seen = set() if seen is None else seen
        if ident in seen:
            raise ValueError('Повреждена история: цикл версий')
        seen = seen | {ident}
        number = event.get('number') or 1 + max((self._generation(p, seen) for p in event.get('parents', []) if p in self.events), default=0)
        cache[ident] = number
        return number

    def _history_name(self, event):
        return 'Версия %06d_%s' % (self._generation(event['id']), event['id'])

    def _history_roots(self, key):
        paths = set(getattr(self, '_history_paths', {}).get(key, ()))
        if key in self.paths:
            paths.add(self.paths[key])
        return [self.path(p).parent / HISTORY_DIR for p in sorted(paths)]

    def _history_folder(self, event):
        return self.path(self.paths.get(event['key'], event['path'])).parent / HISTORY_DIR / self._history_name(event)

    def _assets(self, record):
        result = {}
        if record:
            for node in walk(record['data']):
                for field, hash_field in ASSET_FIELDS:
                    sha, rel = node.get(hash_field), node.get(field)
                    if rel and isinstance(sha, str) and re.fullmatch('[0-9a-f]{64}', sha):
                        result.setdefault(sha, {'sha': sha, 'name': Path(rel).name, 'original': rel})
        return result

    def _scan(self):
        super()._scan()
        self._history_paths = {}
        for event in self.events.values():self._history_paths.setdefault(event['key'], set()).add(event['path'])
        self._history_pending_keys = set()
        # A compacted old node can arrive before its newer child. It is not a
        # deletion of the live card. Keep a read-only projection until delivery.
        for key, ids in self.heads.items():
            pending = [i for i in ids if self.events[i].get('pruned')]
            if not pending:continue
            self._history_pending_keys.add(key)
            candidates = [self.events[i] for i in ids if self.events[i].get('record')]
            frontier = list(pending);seen = set()
            while frontier and not candidates:
                ident = frontier.pop()
                if ident in seen:continue
                seen.add(ident);event = self.events.get(ident, {})
                for parent in event.get('parents', []):
                    node = self.events.get(parent, {})
                    if node.get('record') and not node.get('pruned'):candidates.append(node)
                    else:frontier.append(parent)
            local = self.events[pending[0]]
            try:
                projected = self._read_json(self.path(local['path']))
                if local.get('recordMeta') and digest(projected) == local.get('dataDigest'):
                    candidates = [dict(local, record=dict(local['recordMeta'], data=projected))]
            except (OSError, ValueError):pass
            if candidates:
                chosen = max(candidates, key=lambda e:(e['ts'],e['id']))
                self.latest[key] = chosen['record'];self.paths[key] = chosen['path']
            else:
                event = self.events[pending[0]];meta = event.get('recordMeta')
                if meta and self.path(event['path']).is_file():
                    try:self.latest[key] = dict(meta, data=self._read_json(self.path(event['path'])))
                    except (OSError, ValueError):pass
            self.warnings.append({'key':key,'path':self.paths[key], 'historyPending':True,
                                  'message':'Ожидается следующая версия карточки. Дождитесь синхронизации; редактирование временно недоступно.'})
        self._history_generations = {}
        self._history_pruned = set()
        self._history_markers = []
        folder = self.service / 'Удалённые версии'
        if folder.exists():
            for path in sorted(folder.glob('*.json')):
                try:
                    marker = self._read_json(path)
                    ids, anchors = marker['versions'], marker['anchors']
                    if (not isinstance(ids, list) or not isinstance(anchors, list) or not anchors
                            or not all(isinstance(x, str) and re.fullmatch('[0-9a-f]{32}', x) for x in ids + anchors)
                            or not all(self.events.get(i, {}).get('key') == marker['key'] for i in anchors)):
                        continue  # An out-of-order delivery is not corruption.
                    # Never prune a head: its newer anchor may still be in transit.
                    selected = {i for i in ids if self.events.get(i, {}).get('key') == marker['key']}
                    if selected & set(self.heads.get(marker['key'], [])):
                        continue
                    self._history_pruned.update(selected)
                    self._history_markers.append(marker)
                except (OSError, ValueError, KeyError, TypeError):
                    self.warnings.append({'path': str(path.relative_to(self.root)), 'message': 'Не прочитана отметка удаления версий'})
        self._history_pruned.update(i for i, e in self.events.items() if e.get('pruned'))
        # Position-only changes do not constitute two versions of card contents.
        self.conflicts = [c for c in self.conflicts if len({digest(semantic(v['record'])) for v in c['versions']}) > 1]
        for conflict in self.conflicts:
            for version in conflict['versions']:
                event = self.events[version['id']]
                version.update(pc=event.get('pc', event.get('by', '')), number=self._generation(event['id']))

    def _emit(self, key, record, parents, path):
        path = str(path).replace('\\', '/')
        action = getattr(self, '_history_action', None)
        # A failed projection/save reply must not branch off its own completed event.
        if not action:
            for ident in self.heads.get(key, []):
                event = self.events[ident]
                if event['record'] == record and event['path'] == path:
                    return ident
        number = 1 + max((self._generation(i) for i in parents if i in self.events), default=0)
        event = {'id': uuid.uuid4().hex, 'key': key, 'record': copy.deepcopy(record),
                 'parents': list(parents), 'path': path, 'number': number,
                 'by': getattr(self, '_history_user', '') or self.actor, 'pc': self.actor, 'ts': stamp()}
        parent = next((self.events[i].get('record') for i in parents if i in self.events and self.events[i].get('record')), None)
        event['changedFields'] = [c['field'] for c in differences((parent or {}).get('data', {}), (record or {}).get('data', {}))]
        if action:
            event.update(action)
        atomic(self.events_dir / (event['id'] + '.json'), encode(event))
        self.events[event['id']] = event
        return event['id']

    def _asset_source(self, key, sha):
        cached = getattr(self, '_history_sources', {}).get((key, sha))
        if cached and cached.is_file() and self.hash_file(cached) == sha:
            return cached
        blob = self.blobs / sha
        if blob.is_file() and self.hash_file(blob) == sha:
            return blob
        # A peer may deliver a visible version folder before the blob cache.
        for event in self.events.values():
            if event['key'] != key:
                continue
            for root in self._history_roots(key):
                folder = root / self._history_name(event)
                if folder.is_dir():
                    for path in folder.glob(sha + '_*'):
                        if path.is_file() and self.hash_file(path) == sha:
                            return path
        for record in self.latest.values():
            for asset in self._assets(record).values():
                if asset['sha'] == sha:
                    path = self.path(asset['original'])
                    if path.is_file() and self.hash_file(path) == sha:
                        return path
        return None

    def _sync_history(self, exclude=()):
        self._history_sources = {}
        self._history_waiting_assets = []
        excluded = set(exclude) | getattr(self, '_history_pruned', set())
        groups = {}
        for ident, event in self.events.items():
            if supported(event['key']) and ident not in excluded and not event.get('pruned'):
                groups.setdefault(event['key'], []).append(event)
        for key, events in groups.items():
            owners = {}
            for event in sorted(events, key=lambda e: (self._generation(e['id']), e['ts'], e['id'])):
                folder = self._history_folder(event)
                # Move readable history with a renamed card, without duplicating it.
                for oldroot in self._history_roots(key):
                    old = oldroot / self._history_name(event)
                    if old != folder and old.exists() and not folder.exists():
                        folder.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(old), str(folder))
                        try:oldroot.rmdir()
                        except OSError:pass
                files = []
                for sha, asset in self._assets(event['record']).items():
                    owner, filename = owners.setdefault(sha, (event, sha + '_' + safe(asset['name'])[-45:]))
                    target = self._history_folder(owner) / filename
                    if not target.is_file() or self.hash_file(target) != sha:
                        source = self._asset_source(key, sha)
                        if source:
                            atomic(target, source.read_bytes())
                    ready = target.is_file() and self.hash_file(target) == sha
                    if ready:self._history_sources[(key, sha)] = target
                    else:self._history_waiting_assets.append(target)
                    files.append({**asset, 'sourceVersion': owner['id'], 'file': filename,
                                  'ready': ready})
                manifest = {'id': event['id'], 'number': self._generation(event['id']),
                            'parents': event['parents'], 'ts': event['ts'], 'by': event.get('by', ''),
                            'pc': event.get('pc', event.get('by', '')), 'action': event.get('action', 'edit'),
                            'sourceVersion': event.get('sourceVersion'), 'record': event['record'], 'files': files}
                target = folder / 'Версия.json'
                data = encode(manifest)
                self._write_projection(target, data)
        return groups

    def _checkpoint(self, reason):
        result = super()._checkpoint(reason)
        if reason == 'Автоматически' and result:
            # Card history supplies rollback. Keep one automatic whole-base safety
            # snapshot; explicit user backups are never silently removed.
            for file in self.backups.glob('*.json'):
                if file.name != result['id'] and self._read_json(file).get('reason') == 'Автоматически':
                    file.unlink()
        return result

    def _history_event(self, key, ident):
        event = self.events.get(ident)
        if not event or event['key'] != key or ident in getattr(self, '_history_pruned', set()) or event.get('pruned'):
            raise ValueError('Версия удалена или ещё не синхронизирована. Обновите историю.')
        return event

    def card_history_index(self):
        self.load()
        return [{'key': key, 'title': self._title(record) if record else 'Удалённая карточка',
                 'kind': record['kind'] if record else key.split(':', 1)[0], 'path': self.paths[key],
                 'conflicts': len(self.heads.get(key, [])) if any(c['key'] == key for c in self.conflicts) else 0}
                for key, record in self.latest.items() if supported(key)]

    def history_asset(self, key, ident, sha):
        self.load()
        event = self._history_event(key, ident)
        asset = self._assets(event['record']).get(sha)
        if not asset:raise ValueError('Вложение не относится к выбранной версии')
        source = self._asset_source(key, sha)
        if not source:raise ValueError('Ожидается файл. Дождитесь синхронизации Яндекс Диска.')
        return source, asset['name']

    def card_history(self, key):
        self.load()
        if not supported(key) or key not in self.paths:
            raise ValueError('Карточка не найдена')
        events = [e for e in self.events.values() if e['key'] == key and e['id'] not in self._history_pruned]
        versions = []
        for event in sorted(events, key=lambda e: (self._generation(e['id']), e['ts'], e['id']), reverse=True):
            parent = next((self.events[p].get('record') for p in event['parents'] if p in self.events and self.events[p].get('record')), None)
            changes = differences((parent or {}).get('data', {}), (event['record'] or {}).get('data', {}))
            files = self.card_version(key, event['id'], refresh=False)['files']
            versions.append({'id': event['id'], 'number': self._generation(event['id']),
                             'ts': event['ts'], 'by': event.get('by', ''), 'pc': event.get('pc', event.get('by', '')),
                             'parents': event['parents'], 'action': event.get('action', 'edit'),
                             'sourceVersion': event.get('sourceVersion'), 'current': event['id'] in self.heads.get(key, []),
                             'deleted': event['record'] is None, 'changes': event.get('changedFields', [x['field'] for x in changes]),
                             'ready': all(x['ready'] for x in files), 'files': files})
        return {'key': key, 'path': self.paths[key], 'heads': self.heads.get(key, []),
                'conflict': any(c['key'] == key for c in self.conflicts),
                'pending': key in self._history_pending_keys, 'versions': versions}

    def card_version(self, key, ident, refresh=True):
        if refresh:
            self.load()
        event = self._history_event(key, ident)
        record = copy.deepcopy(event['record'])
        files, paths = [], {}
        for sha, asset in self._assets(record).items():
            source = self._asset_source(key, sha)
            rel = source.relative_to(self.root).as_posix() if source else ''
            paths[sha] = rel
            files.append({'name': asset['name'], 'sha': sha, 'key': rel, 'ready': bool(source),
                          'size': source.stat().st_size if source else 0})
        if record:
            for node in walk(record['data']):
                for field, hash_field in ASSET_FIELDS:
                    if node.get(hash_field) in paths:
                        old = node.get(field)
                        node[field] = paths[node[hash_field]]
                        for image in ('img', 'photo', 'logo', 'sign'):
                            if node.get(image) == old:
                                node[image] = self._image(self.path(node[field])) if node[field] else ''
        current = (self.latest.get(key) or {}).get('data', {})
        return {'id': ident, 'record': record, 'files': files,
                'changes': differences(current, (event['record'] or {}).get('data', {})),
                'ready': all(f['ready'] for f in files)}

    def restore_card_version(self, key, ident, heads=None, resolve=False, user=''):
        self.load()
        if heads is not None and set(heads) != set(self.heads.get(key, [])):
            raise ValueError('Карточка изменилась. Обновите историю перед выбором версии.')
        if key in getattr(self, '_history_pending_keys', set()):raise ValueError('Дождитесь доставки следующих версий карточки')
        conflict = any(c['key'] == key for c in self.conflicts)
        if conflict and not resolve:
            raise ValueError('Сначала выберите итоговую версию конфликта')
        if resolve and ident not in self.heads.get(key, []):
            raise ValueError('Выберите одну из актуальных конфликтующих версий')
        event = self._history_event(key, ident)
        if not event['record']:
            if not resolve:raise ValueError('Это версия удаления карточки; восстановите карточку из корзины')
            self._history_user = user or self.actor
            self._history_action = {'action': 'resolve', 'sourceVersion': ident}
            try:
                path = self.paths[key]
                self._emit(key, None, self.heads[key], path)
                self.path(path).unlink(missing_ok=True)
                return self.load()
            finally:
                self._history_user = '';self._history_action = None
        for sha in self._assets(event['record']):
            source = self._asset_source(key, sha)
            if not source:raise ValueError('Ожидаются файлы этой версии. Дождитесь синхронизации.')
            if not (self.blobs / sha).is_file():atomic(self.blobs / sha, source.read_bytes())
        self._history_user = user or self.actor
        self._history_action = {'action': 'resolve' if resolve else 'restore', 'sourceVersion': ident}
        try:
            record = copy.deepcopy(event['record'])
            # A card rollback does not move it to a deleted/old parent or reorder siblings.
            if self.latest.get(key):
                for field in ('parent', 'position'):
                    if field in self.latest[key]:record[field] = self.latest[key][field]
            self._records = copy.deepcopy(self.latest);self._records[key] = record;self._occupied = {}
            path = self.paths[key]
            self._place(record, path)
            self._emit(key, record, self.heads[key], path)
            self._scan()
            atomic(self.path(path), encode(record['data']))
            self.force.add(key)
            try:return self.load()
            finally:self.force.discard(key)
        finally:
            self._history_action = None;self._history_user = ''

    def resolve(self, key, version):
        return self.restore_card_version(key, version, resolve=True)

    def _prune_selection(self, key, ids, heads=None):
        if not supported(key) or not isinstance(ids, list) or not ids:
            raise ValueError('Выберите версии для удаления')
        if key in getattr(self, '_history_pending_keys', set()):raise ValueError('Дождитесь доставки следующих версий карточки')
        if heads is not None and set(heads) != set(self.heads.get(key, [])):
            raise ValueError('История изменилась. Обновите список версий.')
        selected = [self._history_event(key, i) for i in set(ids)]
        if set(ids) & set(self.heads.get(key, [])):
            raise ValueError('Текущие и конфликтующие версии удалить нельзя. Сначала выберите итоговую версию.')
        return selected

    def _protected_hashes(self, exclude=()):
        needed = set()
        for record in self.latest.values():
            if record:needed.update(self._assets(record))
        for ident, event in self.events.items():
            if ident not in set(exclude) | getattr(self, '_history_pruned', set()) and event.get('record'):
                needed.add(digest(event['record']));needed.update(self._assets(event['record']))
        # Manual backups pin their files, even after a card-history deletion.
        for file in self.backups.glob('*.json'):
            snap = self._read_json(file)
            if snap.get('reason') != 'Автоматически':
                needed.update(snap.get('assets', {}).values());needed.update(snap.get('records', {}).values())
        return needed

    def _prune_info(self, selected):
        ids = {e['id'] for e in selected}
        needed = self._protected_hashes(ids)
        candidates = {h for e in selected for h in self._assets(e.get('record'))}
        candidates.update(digest(e['record']) for e in selected if e.get('record'))
        paths = set()
        for event in selected:
            for root in self._history_roots(event['key']):
                folder = root / self._history_name(event)
                if folder.exists():paths.update(p for p in folder.rglob('*') if p.is_file())
        for sha in candidates - needed:
            paths.update(p for p in (self.blobs / sha, * (self.service / 'Просмотр версий').glob(sha + '*')) if p.is_file())
        # Shared attachments are relocated, so their bytes are not reclaimable.
        kept = {h for e in selected for h in self._assets(e.get('record'))} & needed
        transfer = sum(next((p.stat().st_size for p in paths if p.name.startswith(h + '_')), 0) for h in kept)
        return {'versions': len(ids), 'bytes': max(0, sum(p.stat().st_size for p in paths) - transfer),
                'keptFiles': len(kept), 'candidates': sorted(candidates)}

    def delete_card_versions(self, key, ids, heads=None, preview=False):
        self.load()
        selected = self._prune_selection(key, ids, heads)
        info = self._prune_info(selected)
        if preview:return {**info, 'heads': self.heads[key]}
        # Prove that attachments referenced by surviving versions can be transferred.
        reused = set(info['candidates']) & self._protected_hashes(ids)
        for sha in reused:
            source = self._asset_source(key, sha)
            if source and not (self.blobs / sha).exists():atomic(self.blobs / sha, source.read_bytes())
            if sha in {h for e in selected for h in self._assets(e.get('record'))} and not source:
                raise ValueError('Нельзя удалить версию: используемый файл ещё не синхронизирован')
        self._sync_history(exclude=ids)
        marker = {'id': uuid.uuid4().hex, 'key': key, 'versions': list(set(ids)),
                  'anchors': self.heads[key], 'assets': info['candidates'], 'ts': stamp(),
                  'by': getattr(self, '_history_user', '') or self.actor}
        atomic(self.service / 'Удалённые версии' / (marker['id'] + '.json'), encode(marker))
        self.load()
        return {'deleted': info['versions'], 'state': self.load()['state'], **self._history_result()}

    def _history_result(self):
        return {'revision': self.revision, 'root': str(self.root), 'warnings': self.warnings,
                'conflicts': self.conflicts}

    def _collect_history(self):
        deleted = self._history_pruned
        needed = self._protected_hashes()
        candidates = {h for m in self._history_markers for h in m.get('assets', []) if isinstance(h, str) and re.fullmatch('[0-9a-f]{64}', h)}
        for ident in deleted:
            event = self.events.get(ident)
            if not event or event['key'] in getattr(self, '_history_pending_keys', set()):continue
            # Cache ancestry before replacing the payload; descendants retain stable numbers.
            number = self._generation(ident)
            for root in self._history_roots(event['key']):
                folder = root / self._history_name(event)
                if folder.exists():shutil.rmtree(folder)
            if not event.get('pruned'):
                stub = {k: v for k, v in event.items() if k != 'record'}
                stub.update(record=None, pruned=True, number=number,
                            dataDigest=digest(event['record']['data']) if event.get('record') else None,
                            recordMeta={k:v for k,v in event['record'].items() if k!='data'} if event.get('record') else None,
                            retiredAssets=list(self._assets(event.get('record')).values()))
                atomic(self.events_dir / (ident + '.json'), encode(stub))
                self.events[ident] = stub
        # Automatic snapshots are redundant with per-card history and must not pin
        # attachments explicitly pruned by a user. Manual backups remain intact.
        for file in self.backups.glob('*.json'):
            snap = self._read_json(file)
            refs = set(snap.get('assets', {}).values()) | set(snap.get('records', {}).values())
            if snap.get('reason') == 'Автоматически' and refs & (candidates - needed):file.unlink()
        for sha in candidates - needed:
            (self.blobs / sha).unlink(missing_ok=True)
            for file in (self.service / 'Просмотр версий').glob(sha + '*'):file.unlink()
            # Remove obsolete picker copies as well; live projections are managed
            # by the existing save cleanup and are never deleted by hash alone.
            for file in self.files.glob('*/*'):
                if file.is_file() and self.hash_file(file) == sha:file.unlink()
