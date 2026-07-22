import os
import sys
import smtplib
import ssl

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from app import create_app


def test_smtp():
    app = create_app()
    with app.app_context():
        server   = app.config['MAIL_SERVER']
        port     = app.config['MAIL_PORT']
        use_ssl  = app.config['MAIL_USE_SSL']
        use_tls  = app.config['MAIL_USE_TLS']
        username = app.config['MAIL_USERNAME']
        password = app.config['MAIL_PASSWORD']
        timeout  = app.config.get('MAIL_TIMEOUT', 10)

        print(f"Server  : {server}:{port}")
        print(f"Mode    : {'SSL' if use_ssl else 'STARTTLS' if use_tls else 'plain'}")
        print(f"Account : {username or '(not set)'}")
        print()

        try:
            if use_ssl:
                ctx = ssl.create_default_context()
                smtp = smtplib.SMTP_SSL(server, port, context=ctx, timeout=timeout)
            else:
                smtp = smtplib.SMTP(server, port, timeout=timeout)
                if use_tls:
                    smtp.starttls()

            with smtp:
                print("[OK] Connected to SMTP server.")
                if username and password:
                    smtp.login(username, password)
                    print("[OK] Authentication successful.")
                else:
                    print("[--] No credentials set, skipping login.")

        except smtplib.SMTPAuthenticationError:
            print("[FAIL] Authentication failed — check MAIL_USERNAME / MAIL_PASSWORD.")
            sys.exit(1)
        except (smtplib.SMTPConnectError, ConnectionRefusedError, OSError) as e:
            print(f"[FAIL] Could not connect: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"[FAIL] {type(e).__name__}: {e}")
            sys.exit(1)


if __name__ == "__main__":
    test_smtp()
