// Javascript execution to check version of framer-motion
const fs = require('fs');
const pkg = JSON.parse(fs.readFileSync('frontend/package.json', 'utf8'));
console.log(pkg.dependencies['framer-motion']);
