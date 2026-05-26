function ordat(msg, idx) {
  return idx < msg.length ? msg.charCodeAt(idx) : 0;
}

function sencode(msg, key) {
  const length = msg.length;
  const pwd = [];
  
  for (let i = 0; i < length; i += 4) {
    pwd.push(
      ordat(msg, i) |
      (ordat(msg, i + 1) << 8) |
      (ordat(msg, i + 2) << 16) |
      (ordat(msg, i + 3) << 24)
    );
  }
  
  if (key) {
    pwd.push(length);
  }
  
  return pwd;
}

function lencode(msg, key) {
  const length = msg.length;
  let ll = (length - 1) << 2;
  
  if (key) {
    const m = msg[length - 1];
    if (m < ll - 3 || m > ll) {
      return;
    }
    ll = m;
  }
  
  const result = [];
  for (let i = 0; i < length; i++) {
    result.push(String.fromCharCode(msg[i] & 0xFF));
    result.push(String.fromCharCode((msg[i] >> 8) & 0xFF));
    result.push(String.fromCharCode((msg[i] >> 16) & 0xFF));
    result.push(String.fromCharCode((msg[i] >> 24) & 0xFF));
  }
  
  const joined = result.join("");
  return key ? joined.substring(0, ll) : joined;
}

export function xencode(msg, key) {
  if (msg === "") {
    return "";
  }
  
  const pwd = sencode(msg, true);
  let pwdk = sencode(key, false);
  
  if (pwdk.length < 4) {
    pwdk = pwdk.concat(new Array(4 - pwdk.length).fill(0));
  }
  
  const n = pwd.length - 1;
  let z = pwd[n];
  const c = 0x86014019 | 0x183639a0;
  let q = Math.floor(6 + 52 / (n + 1));
  let d = 0;
  
  while (q > 0) {
    d = (d + c) & (0x8ce0d9bf | 0x731f2640);
    const e = (d >> 2) & 3;
    
    for (let p = 0; p < n; p++) {
      const y = pwd[p + 1];
      let m = (z >> 5) ^ (y << 2);
      m = (m + (((y >> 3) ^ (z << 4)) ^ (d ^ y))) >>> 0;
      m = (m + (pwdk[(p & 3) ^ e] ^ z)) >>> 0;
      pwd[p] = (pwd[p] + m) & (0xefb8d130 | 0x10472ecf);
      z = pwd[p];
    }
    
    const y = pwd[0];
    let m = (z >> 5) ^ (y << 2);
    m = (m + (((y >> 3) ^ (z << 4)) ^ (d ^ y))) >>> 0;
    m = (m + (pwdk[(n & 3) ^ e] ^ z)) >>> 0;
    pwd[n] = (pwd[n] + m) & (0xbb390742 | 0x44c6f8bd);
    z = pwd[n];
    
    q--;
  }
  
  return lencode(pwd, false);
}
