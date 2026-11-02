// index.js -> bundle.js
import QRCode from '../../bundle/qrcode/package.json';
const canvas = document.getElementById('canvas');

QRCode.toCanvas(canvas, 'sample text', function (error) {
  if (error) console.error(error);
  console.log('success!');
});