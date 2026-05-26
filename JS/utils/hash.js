import crypto from "crypto";

export function md5(password, token) {
  return crypto.createHmac("md5", token).update(password).digest("hex");
}
