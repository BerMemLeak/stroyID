"""Current-only storage, safe migration, interrupted writes and explicit snapshots."""

import copy
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from pypdf import PdfReader, PdfWriter
from stroyid.infrastructure.storage import Store, encode
from stroyid.infrastructure.storage.transaction import FileTransaction
from stroyid.application.exports.snapshot import write_snapshot
from test_storage import state, material


class CurrentStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = Store(self.root / "base")

    def tearDown(self):
        self.temp.cleanup()

    def fixture(self):
        data = state()
        data["lib"]["base"] = [material("a", "Труба"), material("b", "Кабель")]
        return self.store.save(data, 0)["state"]

    def test_repeated_saves_keep_one_current_card_and_no_archives(self):
        data = self.fixture()
        for n in range(5):
            data["lib"]["base"][0]["maker"] = str(n)
            data = self.store.save(data, 0)["state"]
        self.assertEqual(Store(self.store.root).load()["state"]["lib"]["base"][0]["maker"], "4")
        files = list(self.store.root.rglob("*"))
        self.assertFalse(
            any("Версии" in p.name or "Резерв" in p.name or p.suffix == ".zip" for p in files)
        )
        self.assertFalse(self.store.transaction.journal.exists())
        self.assertFalse(self.store.transaction.staging.exists())
        self.assertEqual(len(list(self.store.root.rglob("Материал.json"))), 2)

    def test_scheme_versions_and_revision_counters_are_not_persisted(self):
        data = self.fixture()
        data["lib"]["base"][0].update(versions=[{"file": "old.pdf"}], rev=12)
        saved = self.store.save(data, 0)["state"]["lib"]["base"][0]
        self.assertNotIn("versions", saved)
        self.assertNotIn("rev", saved)

    def test_stale_writer_cannot_overwrite_current_card(self):
        base = self.fixture()
        local = copy.deepcopy(base)
        other = Store(self.store.root)
        remote = other.load()["state"]
        remote["lib"]["base"][0]["maker"] = "Другой"
        other.save(remote, 0)
        local["lib"]["base"][0]["maker"] = "Мой"
        with self.assertRaisesRegex(ValueError, "другим пользователем"):
            self.store.save(local, 0, base)
        self.assertEqual(other.load()["state"]["lib"]["base"][0]["maker"], "Другой")

    def test_independent_card_changes_merge(self):
        base = self.fixture()
        other = Store(self.store.root)
        remote = other.load()["state"]
        remote["lib"]["base"][0]["maker"] = "А"
        other.save(remote, 0)
        base["lib"]["base"][1]["maker"] = "Б"
        result = self.store.save(base, 0)["state"]
        self.assertEqual([x["maker"] for x in result["lib"]["base"]], ["А", "Б"])

    def test_corrupt_card_blocks_save_until_explicit_repair(self):
        data = self.fixture()
        path = self.store.path(self.store.paths["base:a"])
        path.write_text("{broken")
        self.assertTrue(self.store.load()["warnings"])
        with self.assertRaises(ValueError):
            self.store.save(data, 0)
        self.assertEqual(path.read_text(), "{broken")
        self.store.repair("base:a", data["lib"]["base"][0])
        self.assertFalse(self.store.load()["warnings"])

    def test_interrupted_write_rolls_forward_after_reopen(self):
        data = self.fixture()
        data["lib"]["base"][0]["maker"] = "После сбоя"
        with patch.object(
            self.store.transaction, "recover", side_effect=[None, None, OSError("Interrupted")]
        ):
            with self.assertRaises(OSError):
                self.store.save(data, 0)
        reopened = Store(self.store.root)
        self.assertEqual(reopened.load()["state"]["lib"]["base"][0]["maker"], "После сбоя")
        self.assertFalse(reopened.transaction.journal.exists())

    def test_cleanup_does_not_follow_retired_directory_symlink(self):
        from stroyid.infrastructure.storage.cleanup import EmptyDirectoryCleaner

        target = self.root / "unrelated"
        target.mkdir()
        link = self.store.root / "retired"
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError:
            self.skipTest("Symlinks unavailable")
        EmptyDirectoryCleaner().clean(self.store.root, ["retired"], {self.store.service})
        self.assertTrue(target.exists())
        self.assertTrue(link.is_symlink())

    def test_abandoned_prejournal_payload_is_discarded_on_reopen(self):
        self.fixture()
        orphan = self.store.transaction.staging / "orphan" / "0"
        orphan.parent.mkdir(parents=True)
        orphan.write_bytes(b"abandoned import")
        reopened = Store(self.store.root)
        self.assertFalse(reopened.transaction.staging.exists())
        self.assertEqual(len(reopened.load()["state"]["lib"]["base"]), 2)

    def test_failed_staging_preserves_current_data(self):
        data = self.fixture()
        data["lib"]["base"][0]["maker"] = "Не записано"
        with patch(
            "stroyid.infrastructure.storage.transaction.atomic", side_effect=OSError("disk full")
        ):
            with self.assertRaises(OSError):
                self.store.save(data, 0)
        self.assertEqual(Store(self.store.root).load()["state"]["lib"]["base"][0]["maker"], "")

    def test_missing_file_is_not_restored_from_hidden_backup(self):
        data = self.fixture()
        source = self.root / "source.pdf"
        source.write_bytes(b"source")
        asset = self.store.import_file(source)
        data["lib"]["base"][0]["docs"] = [
            dict(id="d", type="Паспорт", num="", date="", file=asset["name"], fileKey=asset["id"])
        ]
        data = self.store.save(data, 0)["state"]
        path = self.store.path(data["lib"]["base"][0]["docs"][0]["fileKey"])
        path.unlink()
        loaded = Store(self.store.root).load()
        self.assertTrue(loaded["warnings"])
        self.assertFalse(path.exists())
        with self.assertRaises(ValueError):
            self.store.recover_missing("base:a")


class LegacyMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "base"
        shutil.copytree(Path(__file__).parent / "fixtures/legacy-current", self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_real_previous_format_keeps_current_files_and_removes_old_history(self):
        store = Store(self.root)
        data = store.load()["state"]
        material = data["lib"]["base"][0]
        self.assertEqual(material["maker"], "Текущий")
        self.assertFalse(store.warnings)
        self.assertEqual(
            len(PdfReader(store.asset_path(material["docs"][0]["fileKey"])[0]).pages), 1
        )
        self.assertFalse(
            any(
                "История версий" in p.parts
                or "Резервные копии" in p.parts
                or p.name == "Версии карточек"
                for p in self.root.rglob("*")
            )
        )
        self.assertFalse(json.loads(store.index_path.read_text()).get("legacyCleanup"))
        self.assertEqual(Store(self.root).load()["state"]["projects"][0]["systems"][0]["id"], "s1")

    def test_missing_current_asset_stops_migration_without_deleting_history(self):
        card = next(p for p in self.root.rglob("Материал.json") if "История версий" not in p.parts)
        current = self.root / json.loads(card.read_text())["docs"][0]["fileKey"]
        current.unlink()
        events = self.root / "_Служебное/Версии карточек"
        before = {p.name: p.read_bytes() for p in events.glob("*.json")}
        with self.assertRaises(ValueError):
            Store(self.root)
        self.assertEqual({p.name: p.read_bytes() for p in events.glob("*.json")}, before)
        self.assertFalse((self.root / "_Служебное/Индекс.json").exists())

    def test_changed_card_id_stops_migration_before_deleting_old_files(self):
        card = next(p for p in self.root.rglob("Материал.json") if "История версий" not in p.parts)
        data = json.loads(card.read_text())
        data["id"] = "wrong"
        card.write_bytes(encode(data))
        with self.assertRaisesRegex(ValueError, "id"):
            Store(self.root)
        self.assertTrue((self.root / "_Служебное/Версии карточек").exists())

    def test_failed_history_cleanup_is_retried_on_next_open(self):
        original = shutil.rmtree

        def blocked(path, *args, **kwargs):
            if Path(path).name == "Версии карточек":
                raise PermissionError("Locked")
            return original(path, *args, **kwargs)

        with patch("stroyid.infrastructure.storage.repository.shutil.rmtree", side_effect=blocked):
            with self.assertRaises(PermissionError):
                Store(self.root)
        store = Store(self.root)
        self.assertEqual(store.load()["state"]["lib"]["base"][0]["maker"], "Текущий")
        self.assertFalse((self.root / "_Служебное/Версии карточек").exists())


class SnapshotTests(unittest.TestCase):
    def test_snapshot_has_current_editable_database_and_pdf(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = Store(root / "base")
            data = state()
            data["lib"]["base"] = [material("unused", "Не используется")]
            data = store.save(data, 0)["state"]

            def pdfs(store, plans, prepared, target):
                pdf = root / "Комплект.pdf"
                w = PdfWriter()
                w.add_blank_page(595, 842)
                w.write(pdf)
                with zipfile.ZipFile(target, "w") as archive:
                    archive.write(pdf, pdf.name)

            target = root / "snapshot.zip"
            with (
                patch(
                    "stroyid.application.exports.snapshot.prepare_many",
                    return_value=[{"pages": 1, "documents": 1}],
                ),
                patch("stroyid.application.exports.snapshot.write_many", side_effect=pdfs),
            ):
                write_snapshot(store, data, [{"plan": {}}], target)
            with zipfile.ZipFile(target) as archive:
                self.assertIn("Печать/Комплект.pdf", archive.namelist())
                self.assertFalse(
                    any("Резерв" in n or "История версий" in n for n in archive.namelist())
                )
                archive.extractall(root / "open")
            reopened = Store(root / "open/СтройИД")
            self.assertFalse(reopened.load()["warnings"])
            self.assertEqual(reopened.load()["state"]["lib"]["base"], [])
            self.assertEqual(len(PdfReader(root / "open/Печать/Комплект.pdf").pages), 1)

    def test_render_failure_does_not_replace_existing_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = Store(root / "base")
            data = store.save(state(), 0)["state"]
            target = root / "snapshot.zip"
            target.write_bytes(b"old snapshot")
            with (
                patch("stroyid.application.exports.snapshot.prepare_many", return_value=[]),
                patch(
                    "stroyid.application.exports.snapshot.write_many",
                    side_effect=ValueError("Word unavailable"),
                ),
            ):
                with self.assertRaises(ValueError):
                    write_snapshot(store, data, [{"plan": {}}], target)
            self.assertEqual(target.read_bytes(), b"old snapshot")
