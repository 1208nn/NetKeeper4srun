import crypto from "crypto";
import https from "https";
import http from "http";
import { URL } from "url";
import { logger } from "./utils/logger.js";
import { b64encode } from "./utils/base.js";
import { md5 } from "./utils/hash.js";
import { xencode } from "./utils/xencode.js";
import { devices } from "./utils/device.js";

const HEADERS = {
  "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0",
};

const IP_REGEX =
  /((1\d{2}|25[0-5]|2[0-4]\d|[1-9]?\d)\.){3}(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)/;

const httpRequest = (url, options = {}) =>
  new Promise((resolve, reject) => {
    const parsedUrl = new URL(url);
    const isHttps = parsedUrl.protocol === "https:";
    const transport = isHttps ? https : http;

    const mergedHeaders = { ...HEADERS, ...options.headers };
    const req = transport.request(
      {
        hostname: parsedUrl.hostname,
        port: parsedUrl.port,
        path: parsedUrl.pathname + parsedUrl.search,
        method: options.method || "GET",
        headers: mergedHeaders,
        timeout: 10000,
      },
      (res) => {
        let data = "";
        res.on("data", (chunk) => (data += chunk));
        res.on("end", () => resolve(data));
      }
    );

    req.on("error", reject);
    req.on("timeout", () => {
      req.destroy();
      reject(new Error("Request timeout"));
    });

    if (options.body) req.write(options.body);
    req.end();
  });

class Manager {
  constructor(username = "", password = "") {
    this.acid = 0;
    this.n = "200";
    this.vtype = "1";
    this.encVer = "srun_bx1";
    this.username = username;
    this.password = password;
    this.host = null;
    this.token = null;
    this.checksum = null;
    this.info = null;
  }

  async _getHost(host) {
    try {
      await httpRequest(host);
      this.host = host;
      return host;
    } catch (e) {
      logger.info(`Host ${host} ${e.message}`);
      logger.error("Failed to get host...");
      process.exit(-1);
    }
  }

  async _jsonp(path, params, prefix) {
    const ts = Math.round(Date.now() / 1000);
    const callback = `${prefix}_${ts}`;
    try {
      const url = new URL(this.host + path);
      url.searchParams.set("callback", callback);
      url.searchParams.set("_", ts);
      Object.entries(params).forEach(([key, value]) => {
        url.searchParams.set(key, value);
      });

      const text = await httpRequest(url.toString());
      const json = text.substring(callback.length + 1, text.length - 1);
      return JSON.parse(json);
    } catch (e) {
      logger.error(`JSONP request failed: ${e.message}`);
      throw e;
    }
  }

  async _getIp() {
    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        const resp = await httpRequest(this.host + "/srun_portal_pc");
        const m = resp.match(IP_REGEX);
        if (m) {
          return m[0];
        }
        logger.warn("Failed to find IP in response, retrying...");
        await new Promise((resolve) => setTimeout(resolve, 1000));
      } catch (e) {
        logger.warn(`Attempt ${attempt + 1} failed: ${e.message}`);
      }
    }
    logger.error("Failed to get IP after retries");
    throw new Error("Failed to obtain IP");
  }

  async login() {
    try {
      const ip = await this._getIp();
      const challengeResp = await this._jsonp(
        "/cgi-bin/get_challenge",
        { username: this.username, ip },
        "jQuery1124015280105355320628"
      );
      logger.debug(challengeResp);
      this.token = challengeResp.challenge;
      logger.info(`Token: ${this.token}`);

      this.info =
        "{SRBX1}" +
        b64encode(
          xencode(
            JSON.stringify({
              username: this.username,
              password: this.password,
              ip,
              acid: String(this.acid),
              enc_ver: this.encVer,
            }),
            this.token
          )
        );

      let checksum = this.token + this.username;
      checksum += this.token + md5(this.password, this.token);
      checksum += this.token + String(this.acid);
      checksum += this.token + ip;
      checksum += this.token + this.n;
      checksum += this.token + this.vtype;
      checksum += this.token + this.info;
      this.checksum = crypto.createHash("sha1").update(checksum).digest("hex");

      const device = devices[Math.floor(Math.random() * devices.length)];
      const params = {
        action: "login",
        username: this.username,
        password: "{MD5}" + md5(this.password, this.token),
        os: device[0],
        name: device[1],
        double_stack: "0",
        chksum: this.checksum,
        info: this.info,
        ac_id: String(this.acid),
        ip,
        n: this.n,
        type: this.vtype,
      };

      const result = await this._jsonp(
        "/cgi-bin/srun_portal",
        params,
        "jQuery1124015280105355320628"
      );
      logger.debug(result);

      if (result.suc_msg) {
        logger.info(
          `login: ${result.suc_msg} ${this.username} ${this.password} ${result.online_ip || ""}`
        );
      } else {
        const msg = result.error_msg || "";
        logger.error(`${result.error}: ${msg}`);
        if (msg.includes("BAS") || msg.includes("Nas")) {
          logger.error("ac_id error, retry in 5 seconds...");
          this.acid += 1;
          await new Promise((resolve) => setTimeout(resolve, 5000));
          await this.login();
        } else if (msg.includes("E2901")) {
          logger.error("username or password error...");
        } else if (msg.includes("E2606")) {
          logger.error("user is disabled...");
        }
      }
    } catch (e) {
      logger.error(`Login failed: ${e.message}`);
      throw e;
    }
  }

  async logout() {
    try {
      const t = Math.round(Date.now() / 1000);
      const status = await this.check();
      const username = status.user_name || this.username;
      const ip = status.online_ip || (await this._getIp());

      const sign = crypto
        .createHash("sha1")
        .update(`${t}${username}${ip}1${t}`)
        .digest("hex");

      const params = {
        username,
        ip,
        time: t,
        unbind: "1",
        sign,
      };

      const result = await this._jsonp(
        "/cgi-bin/rad_user_dm",
        params,
        "jQuery112405185119642573086"
      );
      logger.debug(result);
      logger.info(`logout: ${result.error}`);
    } catch (e) {
      logger.error(`Logout failed: ${e.message}`);
      throw e;
    }
  }

  async check() {
    try {
      const result = await this._jsonp(
        "/cgi-bin/rad_user_info",
        {},
        "jQuery112405185119642573086"
      );
      logger.debug(result);
      logger.info(`check: ${result.error}`);
      return result;
    } catch (e) {
      logger.error(`Check failed: ${e.message}`);
      throw e;
    }
  }
}

export default Manager;
