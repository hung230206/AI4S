// A bounded Node worker invoked by the Python API with locally rendered images.
const fs = require('node:fs');
const path = require('node:path');
const {createWorker, PSM} = require('../frontend/node_modules/tesseract.js');
(async () => {
  const request = JSON.parse(fs.readFileSync(0, 'utf8'));
  const models = path.resolve(__dirname, '../.local/ocr-models');
  const languages = {auto: ['eng', 'chi_sim', 'vie'], en: ['eng'], vi: ['vie', 'eng'], zh: ['chi_sim', 'eng']}[request.language] || ['eng', 'chi_sim', 'vie'];
  const worker = await createWorker(languages, 1, {langPath: models, gzip: false, cacheMethod: 'none', logger: () => {}});
  try {
    await worker.setParameters({tessedit_pageseg_mode: PSM.AUTO, user_defined_dpi: '200'});
    const pages = [];
    for (const filename of request.images) {
      const {data} = await worker.recognize(filename);
      pages.push({text: data.text, confidence: data.confidence});
    }
    process.stdout.write(JSON.stringify({pages}));
  } finally {await worker.terminate();}
})().catch(() => {process.stderr.write('Local OCR worker failed'); process.exit(1);});
