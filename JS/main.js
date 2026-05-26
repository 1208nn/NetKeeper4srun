import fs from "fs";
import Manager from "./manager.js";
import { logger } from "./utils/logger.js";

async function main() {
  try {
    const authData = fs.readFileSync("srun_auth.json", "utf-8");
    const auth = JSON.parse(authData);

    logger.info("Process started");

    const manager = new Manager(auth.username, auth.password);
    await manager._getHost("http://192.168.210.175");
    
    await manager.logout();
    await manager.login();
    
    const status = await manager.check();
    if (status.error !== "ok") {
      logger.warn(`${status.error}, try to login...`);
      await manager.login();
    }
  } catch (e) {
    if (e.code === "ENOENT") {
      logger.error(
        `${e.message}, please check srun_auth.json`
      );
    } else {
      logger.error(`Error: ${e.message}`);
    }
    process.exit(-1);
  }
}

main();
