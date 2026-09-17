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

function buildHoverMap(entries) {
  const map = new Map();
  for (const e of entries) {
    if (e.documentation) map.set(e.name.toLowerCase(), e.documentation);
  }
  return map;
}

const FUNCTION_HOVER = buildHoverMap(FUNCTIONS);
const KEYWORD_HOVER = buildHoverMap(KEYWORDS);

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

function provideHover(document, position) {
  const range = document.getWordRangeAtPosition(position, /\$?\w+/);
  if (!range) return undefined;
  const word = document.getText(range).toLowerCase();
  const text = FUNCTION_HOVER.get(word) ?? KEYWORD_HOVER.get(word);
  if (!text) return undefined;
  return new vscode.Hover(text, range);
}

function toDocTreeItem(rec, iconId) {
  const item = new vscode.TreeItem(rec.filterText);
  if (rec.detail) item.tooltip = new vscode.MarkdownString(rec.detail);
  item.command = { command: 'vgr.showDoc', title: 'Show Documentation', arguments: [rec.filterText] };
  item.iconPath = new vscode.ThemeIcon(iconId);
  return item;
}

class VgrReferenceProvider {
  getTreeItem(el) { return el; }
  getChildren() {
    return [
      ...FUNCTION_ITEMS.filter(f => f.documentation || f.detail).map(f => toDocTreeItem(f, 'symbol-function')),
      ...KEYWORD_ITEMS.filter(k => k.documentation || k.detail).map(k => toDocTreeItem(k, 'symbol-keyword')),
    ];
  }
}

function nameFromDocUri(uri) {
  return uri.path.replace(/^\//, '').replace(/\.md$/, '');
}

class VgrDocProvider {
  provideTextDocumentContent(uri) {
    const name = nameFromDocUri(uri)
    const rec = [...FUNCTION_ITEMS, ...KEYWORD_ITEMS].find(r => r.filterText === name);
    if (!rec) return `No documentation for ${name}`;
    const doc = rec.documentation instanceof vscode.MarkdownString
      ? rec.documentation.value : (rec.documentation || rec.detail || `No documentation for ${name}`);
    return `# ${rec.filterText}\n\n${doc}`;
  }
}

let vgrTerminal;
vscode.window.onDidCloseTerminal(terminal => {
  if (terminal === vgrTerminal) vgrTerminal = undefined;
});

function getVgrTerminal() {
    if (vgrTerminal) return vgrTerminal;
    vgrTerminal = vscode.window.terminals.find(
        terminal => terminal.name === 'VGR'
    );
    if (!vgrTerminal) vgrTerminal = vscode.window.createTerminal('VGR');
    return vgrTerminal;
}

async function getPython(resource) {
  const pythonExtension = vscode.extensions.getExtension('ms-python.python');
  if (!pythonExtension) return 'python3';
  const pythonApi = await pythonExtension.activate();
  const environment = pythonApi.environments.getActiveEnvironmentPath(resource);
  return environment?.path || 'python3';
}

function activate(context) {
  context.subscriptions.push(
    vscode.languages.registerCompletionItemProvider({ language: 'vgr' }, { provideCompletionItems }),
    //-----
    vscode.languages.registerHoverProvider({ language: 'vgr' }, { provideHover }),
        vscode.workspace.registerTextDocumentContentProvider('vgr-doc', new VgrDocProvider()),
    //-----
    vscode.commands.registerCommand('vgr.showDoc', async (name) => {
      const uri = vscode.Uri.parse(`vgr-doc:${name}.md`);
      await vscode.workspace.openTextDocument(uri); // forces our provider to run, registers the doc
      await vscode.commands.executeCommand('markdown.showPreviewToSide', uri);
    }),
    //-----
    vscode.commands.registerCommand('vgr.runFile', async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) return;
      const terminal = getVgrTerminal();
      terminal.show();
      const python = await getPython(editor.document.uri);
      terminal.sendText(`${python} -m vgr --file "${editor.document.uri.fsPath}"`);
    }),
    //-----
    vscode.commands.registerCommand('vgr.startRepl', async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) return;
      const terminal = vscode.window.createTerminal({ name: 'VGR REPL', });
      terminal.show();
      const python = await getPython(editor.document.uri);
      terminal.sendText(`${python} -m vgr`);
    }),
  );
  vscode.window.registerTreeDataProvider('vgrReference', new VgrReferenceProvider());
}

module.exports = { activate, deactivate() {} };
