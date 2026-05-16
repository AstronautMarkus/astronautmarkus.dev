import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from app import create_app
from app.storage import storage


TEST_PATH = "_test/storage_test_probe.txt"
TEST_CONTENT = b"storage probe ok"


def _ok(msg):  print(f"[OK]   {msg}")
def _fail(msg, exc=None):
    print(f"[FAIL] {msg}")
    if exc:
        print(f"       {type(exc).__name__}: {exc}")


def test_storage():
    app = create_app()
    with app.app_context():
        driver = app.config.get('STORAGE_DRIVER', 'local').lower()

        # ── Config summary ────────────────────────────────────────────────────
        print(f"Driver  : {driver.upper()}")
        if driver == 's3':
            print(f"Bucket  : {app.config.get('STORAGE_S3_BUCKET')}")
            print(f"Region  : {app.config.get('STORAGE_S3_REGION')}")
            endpoint = app.config.get('STORAGE_S3_ENDPOINT')
            if endpoint:
                print(f"Endpoint: {endpoint}")
        else:
            print(f"Root    : {app.config.get('STORAGE_LOCAL_ROOT')}")
        print()

        passed = 0
        failed = 0

        # ── 1. put ────────────────────────────────────────────────────────────
        try:
            storage.put(TEST_PATH, TEST_CONTENT)
            _ok(f"put({TEST_PATH!r})")
            passed += 1
        except Exception as e:
            _fail(f"put({TEST_PATH!r})", e)
            failed += 1

        # ── 2. exists → True ─────────────────────────────────────────────────
        try:
            assert storage.exists(TEST_PATH), "exists() returned False after put()"
            _ok(f"exists({TEST_PATH!r}) → True")
            passed += 1
        except Exception as e:
            _fail(f"exists({TEST_PATH!r})", e)
            failed += 1

        # ── 3. get ────────────────────────────────────────────────────────────
        try:
            data = storage.get(TEST_PATH)
            assert data == TEST_CONTENT, f"content mismatch: {data!r}"
            _ok(f"get({TEST_PATH!r}) → content matches")
            passed += 1
        except Exception as e:
            _fail(f"get({TEST_PATH!r})", e)
            failed += 1

        # ── 4. url ────────────────────────────────────────────────────────────
        try:
            url = storage.url(TEST_PATH)
            assert isinstance(url, str) and url, "url() returned empty string"
            _ok(f"url({TEST_PATH!r}) → {url}")
            passed += 1
        except Exception as e:
            _fail(f"url({TEST_PATH!r})", e)
            failed += 1

        # ── 5. list ───────────────────────────────────────────────────────────
        try:
            files = storage.list(prefix="_test/")
            assert TEST_PATH in files, f"{TEST_PATH!r} not in list result: {files}"
            _ok(f"list(prefix='_test/') → {len(files)} file(s), probe found")
            passed += 1
        except Exception as e:
            _fail("list(prefix='_test/')", e)
            failed += 1

        # ── 6. delete ─────────────────────────────────────────────────────────
        try:
            assert storage.delete(TEST_PATH), "delete() returned False"
            _ok(f"delete({TEST_PATH!r})")
            passed += 1
        except Exception as e:
            _fail(f"delete({TEST_PATH!r})", e)
            failed += 1

        # ── 7. exists → False after delete ───────────────────────────────────
        try:
            assert not storage.exists(TEST_PATH), "exists() still True after delete()"
            _ok(f"exists({TEST_PATH!r}) → False after delete")
            passed += 1
        except Exception as e:
            _fail(f"exists after delete({TEST_PATH!r})", e)
            failed += 1

        # ── Summary ───────────────────────────────────────────────────────────
        print()
        print(f"Results : {passed} passed, {failed} failed")

        if failed:
            sys.exit(1)


if __name__ == "__main__":
    test_storage()
