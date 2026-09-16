const vscode = require('vscode');

const KEYWORDS = require('./keywords.json');
const KEYWORD_LOWER_SET = new Set(KEYWORDS.map(k => k.name.toLowerCase()));
const KEYWORD_ITEMS = KEYWORDS.map(rec => {
  const item = new vscode.CompletionItem(rec.name, vscode.CompletionItemKind.Keyword);
  item.filterText = rec.name;
  item.insertText = new vscode.SnippetString(rec.insertText ? insertText : `${rec.name}`);
  if (rec.detail) item.detail = rec.detail;
  if (rec.documentation) item.documentation = new vscode.MarkdownString(rec.documentation);
  return item;
});

const FUNCTIONS = require('./functions.json');
const FUNCTION_LOWER_SET = new Set(FUNCTIONS.map(f => f.name.toLowerCase()));
const FUNCTION_ITEMS = FUNCTIONS.map(rec => {
  const item = new vscode.CompletionItem(rec.name, vscode.CompletionItemKind.Function);
  item.filterText = rec.name;
  item.insertText = new vscode.SnippetString(rec.insertText ? insertText : `${rec.name}()`);
  if (rec.detail) item.detail = rec.detail;
  if (rec.documentation) item.documentation = new vscode.MarkdownString(rec.documentation);
  return item;
});

function stripComments(text) {
  return text
    .replace(/\/\*[\s\S]*?\*\//g, ' ')   // block comments — do this first
    .replace(/(#|\/\/).*$/gm, ' ');      // line comments to EOL
}

function classifyContext(line) {
  const m = /([.@(])\s*\$?\w*$/.exec(line);
  return m ? m[1] : null;
}

function getDocWordItems(document) {
  const cleanText = stripComments(document.getText());
  // A very rough approximation of what our variables might look like
  // but will include other text from inside strings and even regex constants
  const docWords = new Set(cleanText.match(/[\w\$][\w\-]+\w/g) || []);
  return [...docWords]
    .filter(w => !KEYWORD_LOWER_SET.has(w.toLowerCase()))
    .filter(w => !FUNCTION_LOWER_SET.has(w.toLowerCase()))
    .map(w => {
      const item = new vscode.CompletionItem(w, vscode.CompletionItemKind.Text);
      item.filterText = w;
      return item;
    });
}

function provideCompletionItems(document, position, token, context) {
  const line = document.lineAt(position.line).text.slice(0, position.character);
  const ctx = classifyContext(line);
  // They are trying to composose a user function call (but could be @Import too)
  // very likely they'll just want an extracted variable name
  if (ctx === '@') return getDocWordItems(document);
  // They are going to do another deref step, call a built-in, or nest an expression
  // So everything except keywords
  if (ctx === '.' || ctx === '(') return [...FUNCTION_ITEMS, ...getDocWordItems(document)];
  // Everything else we suggest keywords, function, or "text"
  return [...KEYWORD_ITEMS, ...FUNCTION_ITEMS, ...getDocWordItems(document)];
}

function activate(context) {
  context.subscriptions.push(
    vscode.languages.registerCompletionItemProvider({ language: 'vgr' }, { provideCompletionItems })
  );
}

module.exports = { activate, deactivate() {} };
