const fs = require('fs');
const path = require('path');

const blacklist = ['templates', '__pycache__', 'blueprints', 'schemas', 'database.db'];

function readFiles(dir, fileCallback) {
  fs.readdirSync(dir).forEach(file => {
    const filePath = path.join(dir, file);
    const isBlacklisted = blacklist.includes(file);
    if (isBlacklisted) {
      //console.log(`Skipping blacklisted folder: ${filePath}`);
      return;
    }
    const stat = fs.statSync(filePath);
    if (stat.isDirectory()) {
      readFiles(filePath, fileCallback);
    } else {
      const contents = fs.readFileSync(filePath, 'utf8');
      fileCallback(filePath, contents);
    }
  });
}

// Example usage:
const rootDir = './mygptapp';
readFiles(rootDir, (filePath, contents) => {
  console.log(`----------`)
  console.log(`Contents of file ${filePath}:`);
  console.log(`----------`)
  console.log(contents);
  console.log(`----------`)
  console.log(`End of file ${filePath}`)
  console.log(`----------`)
});
