import { deflateSync } from 'node:zlib';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const outputPath = resolve(__dirname, '../src-tauri/icons/source.png');
const size = 1024;

function crc32(buffer) {
  let crc = 0xffffffff;
  for (const byte of buffer) {
    crc ^= byte;
    for (let i = 0; i < 8; i += 1) {
      crc = (crc >>> 1) ^ (0xedb88320 & -(crc & 1));
    }
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function chunk(type, data) {
  const typeBuffer = Buffer.from(type);
  const length = Buffer.alloc(4);
  const checksum = Buffer.alloc(4);
  length.writeUInt32BE(data.length);
  checksum.writeUInt32BE(crc32(Buffer.concat([typeBuffer, data])));
  return Buffer.concat([length, typeBuffer, data, checksum]);
}

function insideRoundedRect(x, y, left, top, width, height, radius) {
  const right = left + width;
  const bottom = top + height;
  if (x < left || x >= right || y < top || y >= bottom) return false;
  const nearLeft = x < left + radius;
  const nearRight = x >= right - radius;
  const nearTop = y < top + radius;
  const nearBottom = y >= bottom - radius;
  if (!(nearLeft || nearRight) || !(nearTop || nearBottom)) return true;
  const cx = nearLeft ? left + radius : right - radius - 1;
  const cy = nearTop ? top + radius : bottom - radius - 1;
  return (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2;
}

function drawRect(pixels, left, top, width, height, color) {
  const [r, g, b, a] = color;
  const right = Math.min(size, left + width);
  const bottom = Math.min(size, top + height);
  for (let y = Math.max(0, top); y < bottom; y += 1) {
    for (let x = Math.max(0, left); x < right; x += 1) {
      const index = (y * size + x) * 4;
      pixels[index] = r;
      pixels[index + 1] = g;
      pixels[index + 2] = b;
      pixels[index + 3] = a;
    }
  }
}

function drawDiagonal(pixels, x1, y1, x2, y2, thickness, color) {
  const [r, g, b, a] = color;
  const dx = x2 - x1;
  const dy = y2 - y1;
  const lengthSquared = dx * dx + dy * dy;
  const radiusSquared = thickness * thickness;

  for (let y = 220; y < 760; y += 1) {
    for (let x = 170; x < 570; x += 1) {
      const t = Math.max(0, Math.min(1, ((x - x1) * dx + (y - y1) * dy) / lengthSquared));
      const px = x1 + t * dx;
      const py = y1 + t * dy;
      if ((x - px) ** 2 + (y - py) ** 2 <= radiusSquared) {
        const index = (y * size + x) * 4;
        pixels[index] = r;
        pixels[index + 1] = g;
        pixels[index + 2] = b;
        pixels[index + 3] = a;
      }
    }
  }
}

const pixels = Buffer.alloc(size * size * 4);

for (let y = 0; y < size; y += 1) {
  for (let x = 0; x < size; x += 1) {
    const index = (y * size + x) * 4;
    const nx = x / (size - 1);
    const ny = y / (size - 1);
    const rounded = insideRoundedRect(x, y, 48, 48, 928, 928, 176);
    pixels[index] = rounded ? Math.round(22 + 26 * nx) : 0;
    pixels[index + 1] = rounded ? Math.round(88 + 84 * ny) : 0;
    pixels[index + 2] = rounded ? Math.round(190 + 34 * (1 - nx)) : 0;
    pixels[index + 3] = rounded ? 255 : 0;
  }
}

const white = [255, 255, 255, 255];
const cyan = [125, 211, 252, 255];

drawDiagonal(pixels, 214, 720, 362, 300, 38, white);
drawDiagonal(pixels, 506, 720, 362, 300, 38, white);
drawRect(pixels, 270, 548, 184, 70, white);
drawRect(pixels, 642, 292, 80, 428, white);
drawRect(pixels, 612, 292, 140, 74, white);
drawRect(pixels, 612, 646, 140, 74, white);
drawRect(pixels, 790, 292, 74, 428, cyan);

const raw = Buffer.alloc((size * 4 + 1) * size);
for (let y = 0; y < size; y += 1) {
  raw[y * (size * 4 + 1)] = 0;
  pixels.copy(raw, y * (size * 4 + 1) + 1, y * size * 4, (y + 1) * size * 4);
}

const ihdr = Buffer.alloc(13);
ihdr.writeUInt32BE(size, 0);
ihdr.writeUInt32BE(size, 4);
ihdr[8] = 8;
ihdr[9] = 6;

const png = Buffer.concat([
  Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
  chunk('IHDR', ihdr),
  chunk('IDAT', deflateSync(raw, { level: 9 })),
  chunk('IEND', Buffer.alloc(0))
]);

mkdirSync(dirname(outputPath), { recursive: true });
writeFileSync(outputPath, png);
console.log(`Generated ${outputPath}`);
