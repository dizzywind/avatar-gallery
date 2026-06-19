const http = require('http');
const fs = require('fs');
const path = require('path');

const server = http.createServer((req, res) => {
  try {
    const url = new URL(req.url, 'http://localhost');
    let filePath = '.' + url.pathname;
    if (filePath === './' || filePath === '') filePath = './index.html';

    if (url.pathname === '/delete-manifest') {
      const selected = (url.searchParams.get('selected') || '').split(',').filter(Boolean);
      const data = JSON.parse(fs.readFileSync('./data.json', 'utf8'));
      const known = new Set((data.avatars || []).map(a => a.filename));
      const manifest = selected.filter(f => known.has(f)).map(filename => ({ filename, action: 'delete' }));
      if (selected.length && !manifest.length) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'no known filenames' }));
        return;
      }
      const updated = (data.avatars || []).filter(a => !manifest.some(m => m.filename === a.filename));
      fs.writeFileSync('./data.json', JSON.stringify({ avatars: updated }, null, 2));
      res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', 'Content-Disposition': 'attachment; filename="data.json"' });
      res.end(JSON.stringify({ avatars: updated }, null, 2));
      return;
    }

    const ext = path.extname(filePath);
    const contentTypes = {
      '.html': 'text/html',
      '.css': 'text/css',
      '.js': 'application/javascript',
      '.json': 'application/json',
      '.jpg': 'image/jpeg',
      '.png': 'image/png'
    };

    fs.readFile(filePath, (err, content) => {
      if (err) {
        res.writeHead(404);
        res.end('Not found');
        return;
      }
      res.writeHead(200, { 'Content-Type': contentTypes[ext] || 'text/plain' });
      res.end(content);
    });
  } catch (err) {
    res.writeHead(500);
    res.end(String(err.message));
  }
});

server.listen(3000, () => console.log('Gallery server on http://localhost:3000'));
