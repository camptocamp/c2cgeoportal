"use strict";
let async = require('async');
let fs = require('fs');
let options = require('commander');
let Extractor = require('angular-gettext-tools').Extractor;

function main(inputs) {
  let extractor = new Extractor();

  async.eachSeries(inputs,
    function(input, cb) {
      fs.readFile(input, {encoding: 'utf-8'}, function(err, data) {
        if (!err) {
          extractor.parse(input, data);
        }
        cb(err);
      });
    },
    function(err) {
      if (err) {
        throw new Error(err);
      }
      let messages = [];
      for (let msgstr in extractor.strings) {
        if (extractor.strings.hasOwnProperty(msgstr)) {
          let msg = extractor.strings[msgstr];
          let contexts = Object.keys(msg).sort();
          let ref = msg[contexts]['references'].join(', ');
          messages.push([ref, msgstr]);
        }
      }

      process.stdout.write(JSON.stringify(messages));
    }
  );
}

// If running this module directly then call the main function.
if (require.main === module) {
  options.parse(process.argv);
  main(options.args);
}

module.exports = main;
