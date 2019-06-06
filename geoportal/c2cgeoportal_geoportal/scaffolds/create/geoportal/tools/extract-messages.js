const fs = require('fs');
const options = require('commander');
const Extractor = require('angular-gettext-tools').Extractor;

function main(inputs) {
  const extractor = new Extractor();

  const promises = [];
  inputs.forEach((input) => {
    promises.push(new Promise((resolve) => {
      fs.readFile(input, 'utf-8', (error, content) => {
        resolve(error ? undefined : {input, content});
      });
    }));
  });

  const messages = [];
  Promise.all(promises).then((contents) => {
    contents = contents.filter(content => content !== undefined);
    contents.forEach(({input, content}) => extractor.parse(input, content));
    for (const msgstr in extractor.strings) {
      if (extractor.strings.hasOwnProperty(msgstr)) {
        const msg = extractor.strings[msgstr];
        const contexts = Object.keys(msg).sort();
        const ref = msg[contexts]['references'].join(', ');
        messages.push([ref, msgstr]);
      }
    }
    process.stdout.write(JSON.stringify(messages));
  });
}

// If running this module directly then call the main function.
if (require.main === module) {
  options.parse(process.argv);
  main(options.args);
}

module.exports = main;
