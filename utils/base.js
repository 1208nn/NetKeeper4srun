const PADCHAR = "=";
const ALPHA = "LVoJPiCN2R8G90yg+hmFHuacZ1OWMnrsSTXkYpUq/3dlbfKwv6xztjI7DeBE45QA";

export function b64encode(s) {
  const x = [];
  const imax = s.length - (s.length % 3);
  
  if (s.length === 0) {
    return s;
  }
  
  for (let i = 0; i < imax; i += 3) {
    const b10 = (s.charCodeAt(i) << 16) | (s.charCodeAt(i + 1) << 8) | s.charCodeAt(i + 2);
    x.push(ALPHA[(b10 >> 18)]);
    x.push(ALPHA[((b10 >> 12) & 63)]);
    x.push(ALPHA[((b10 >> 6) & 63)]);
    x.push(ALPHA[(b10 & 63)]);
  }
  
  const i = imax;
  if (s.length - imax === 1) {
    const b10 = s.charCodeAt(i) << 16;
    x.push(ALPHA[(b10 >> 18)] + ALPHA[((b10 >> 12) & 63)] + PADCHAR + PADCHAR);
  } else if (s.length - imax === 2) {
    const b10 = (s.charCodeAt(i) << 16) | (s.charCodeAt(i + 1) << 8);
    x.push(
      ALPHA[(b10 >> 18)] +
      ALPHA[((b10 >> 12) & 63)] +
      ALPHA[((b10 >> 6) & 63)] +
      PADCHAR
    );
  }
  
  return x.join("");
}
