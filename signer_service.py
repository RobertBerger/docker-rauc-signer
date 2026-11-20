import os, subprocess, tempfile, threading
from flask import Flask, request, send_file, abort

app = Flask(__name__)
lock = threading.Lock()

KEYRING_PATH       = "/etc/ssl/certs/res-ca-chain.pem"
INTERMEDIATE_PATH  = "/keys/rauc-dev/ca-chain.pem"

PKCS11_CERT_PROD   = "pkcs11:id=%02;type=cert"
PKCS11_KEY_PROD    = "pkcs11:id=%02;type=private"
PKCS11_CERT_UNLOCK = "pkcs11:id=%03;type=cert"
PKCS11_KEY_UNLOCK  = "pkcs11:id=%03;type=private"


@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200

@app.route("/sign/rauc/<mode>", methods=["POST"])
def sign_rauc(mode):
    if mode not in ("dev", "prod", "unlock"):
        abort(400, "Mode must be dev, prod, or unlock")
    if "bundle" not in request.files:
        abort(400, "Missing 'bundle' file upload")

    with tempfile.TemporaryDirectory() as tmp:
        in_path  = os.path.join(tmp, "input.raucb")
        out_path = os.path.join(tmp, "signed.raucb")
        request.files["bundle"].save(in_path)

        env = os.environ.copy()
        base_cmd = [
            "rauc",
            "-C", "keyring:check-purpose=codesign-rauc",
            "resign",
            f"--keyring={KEYRING_PATH}",
            f"--intermediate={INTERMEDIATE_PATH}",
        ]

        if mode == "dev":
            cmd = base_cmd + [
                "--cert=/keys/rauc-dev/rauc-dev.cert.pem",
                "--key=/keys/rauc-dev/rauc-dev.key.pem",
                in_path, out_path
            ]
        elif mode == "prod":
            pin = os.environ.get("YK_PIN", "")
            env["RAUC_PKCS11_PIN"] = pin
            env["RAUC_PKCS11_MODULE"] = "/usr/lib/x86_64-linux-gnu/opensc-pkcs11.so"
            cmd = base_cmd + [
                "--cert=pkcs11:id=%02;type=cert",
                f"--key=pkcs11:id=%02;type=private?pin-value={pin}",
                in_path, out_path
            ]
        else:  # unlock
            pin = os.environ.get("YK_PIN", "")
            env["RAUC_PKCS11_PIN"] = pin
            env["RAUC_PKCS11_MODULE"] = "/usr/lib/x86_64-linux-gnu/opensc-pkcs11.so"
            cmd = base_cmd + [
                "--cert=pkcs11:id=%03;type=cert",
                f"--key=pkcs11:id=%03;type=private?pin-value={pin}",
                in_path, out_path
            ]
        with lock:
            res = subprocess.run(
                cmd,
                env=env,
                input=f"{pin}\n" if mode in ("prod", "unlock") else None,
                capture_output=True,
                text=True
            )

            if res.returncode != 0:
                print(f"[ERROR] {mode} resign failed: {res.stderr}", flush=True)
                abort(500, f"rauc resign failed: {res.stderr}")

        return send_file(out_path, as_attachment=True, download_name="signed.raucb")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9998)

