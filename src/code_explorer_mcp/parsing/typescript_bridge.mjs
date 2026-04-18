import { Project, ScriptKind, SyntaxKind } from "../../ts_parser_poc/node_modules/ts-morph/dist/ts-morph.js";

const SYMBOL_TYPES = [
  "imports",
  "globals",
  "classes",
  "functions",
  "interfaces",
  "type_aliases",
  "enums",
  "re_exports",
];

function lineAndColumn(sourceFile, position) {
  const lineAndColumn = sourceFile.getLineAndColumnAtPos(position);
  return {
    line: lineAndColumn.line,
    column: lineAndColumn.column - 1,
  };
}

function makeSpan(sourceFile, node) {
  return {
    start: lineAndColumn(sourceFile, node.getStart()),
    end: lineAndColumn(sourceFile, node.getEnd()),
  };
}

function addSymbolSpan(symbolSpans, sourceFile, symbol, symbolType, node) {
  if (symbolSpans[symbol]) {
    return;
  }

  symbolSpans[symbol] = {
    symbol_type: symbolType,
    span: makeSpan(sourceFile, node),
  };
}

function isExported(node) {
  if (typeof node.isExported === "function") {
    return node.isExported();
  }
  return false;
}

function parseImports(sourceFile) {
  return sourceFile.getImportDeclarations().map((declaration) => {
    const defaultImport = declaration.getDefaultImport();
    const namespaceImport = declaration.getNamespaceImport();
    const namedImports = declaration
      .getNamedImports()
      .map((specifier) => specifier.getAliasNode()?.getText() ?? specifier.getName())
      .sort((left, right) => left.localeCompare(right));

    return {
      module: declaration.getModuleSpecifierValue(),
      default: defaultImport?.getText() ?? null,
      namespace: namespaceImport?.getText() ?? null,
      named: namedImports,
    };
  });
}

function parseGlobals(sourceFile, symbolSpans) {
  const globals = [];

  for (const statement of sourceFile.getVariableStatements()) {
    if (!isExported(statement)) {
      continue;
    }

    for (const declaration of statement.getDeclarations()) {
      const nameNode = declaration.getNameNode();
      if (!nameNode || nameNode.getKind() !== SyntaxKind.Identifier) {
        continue;
      }

      const name = declaration.getName();
      globals.push({
        name,
        declaration_kind: statement.getDeclarationKind(),
      });
      addSymbolSpan(symbolSpans, sourceFile, name, "globals", declaration);
    }
  }

  return globals;
}

function parseFunctions(sourceFile, symbolSpans) {
  const functions = [];

  for (const declaration of sourceFile.getFunctions()) {
    if (!isExported(declaration)) {
      continue;
    }

    const name = declaration.getName();
    if (!name) {
      continue;
    }

    functions.push({ name, syntax: "function" });
    addSymbolSpan(symbolSpans, sourceFile, name, "functions", declaration);
  }

  for (const statement of sourceFile.getVariableStatements()) {
    if (!isExported(statement)) {
      continue;
    }

    for (const declaration of statement.getDeclarations()) {
      const nameNode = declaration.getNameNode();
      if (!nameNode || nameNode.getKind() !== SyntaxKind.Identifier) {
        continue;
      }

      const initializer = declaration.getInitializer();
      if (!initializer || initializer.getKind() !== SyntaxKind.ArrowFunction) {
        continue;
      }

      const name = declaration.getName();
      functions.push({ name, syntax: "arrow" });
      addSymbolSpan(symbolSpans, sourceFile, name, "functions", declaration);
    }
  }

  return functions;
}

function parseInterfaceDeclaration(declaration, sourceFile, symbolSpans) {
  const name = declaration.getName();
  addSymbolSpan(symbolSpans, sourceFile, name, "interfaces", declaration);
  return {
    name,
  };
}

function parseTypeAliasDeclaration(declaration, sourceFile, symbolSpans) {
  const name = declaration.getName();
  addSymbolSpan(symbolSpans, sourceFile, name, "type_aliases", declaration);
  return {
    name,
  };
}

function parseEnumDeclaration(declaration, sourceFile, symbolSpans) {
  const name = declaration.getName();
  addSymbolSpan(symbolSpans, sourceFile, name, "enums", declaration);
  return {
    name,
  };
}

function parseClassExpression(expression, sourceFile, symbolSpans, dottedPrefix) {
  const members = [];
  const methods = [];
  const accessors = [];
  const innerClasses = [];

  for (const member of expression.getMembers()) {
    if (member.getKind() === SyntaxKind.PropertyDeclaration) {
      const nameNode = member.getNameNode();
      if (!nameNode || nameNode.getKind() !== SyntaxKind.Identifier) {
        continue;
      }

      const memberName = member.getName();
      const dottedName = `${dottedPrefix}.${memberName}`;
      const initializer = member.getInitializer();
      if (initializer && initializer.getKind() === SyntaxKind.ClassExpression) {
        innerClasses.push(
          parseClassExpression(initializer, sourceFile, symbolSpans, dottedName),
        );
        addSymbolSpan(symbolSpans, sourceFile, dottedName, "classes", initializer);
        continue;
      }

      members.push({ name: memberName });
      addSymbolSpan(symbolSpans, sourceFile, dottedName, "classes", member);
      continue;
    }

    if (member.getKind() === SyntaxKind.MethodDeclaration) {
      const nameNode = member.getNameNode();
      if (!nameNode || nameNode.getKind() !== SyntaxKind.Identifier) {
        continue;
      }

      const memberName = member.getName();
      methods.push({ name: memberName });
      addSymbolSpan(
        symbolSpans,
        sourceFile,
        `${dottedPrefix}.${memberName}`,
        "classes",
        member,
      );
      continue;
    }

    if (
      member.getKind() === SyntaxKind.GetAccessor ||
      member.getKind() === SyntaxKind.SetAccessor
    ) {
      const nameNode = member.getNameNode();
      if (!nameNode || nameNode.getKind() !== SyntaxKind.Identifier) {
        continue;
      }

      const memberName = member.getName();
      const kind = member.getKind() === SyntaxKind.GetAccessor ? "getter" : "setter";
      accessors.push({ name: memberName, kind });
      addSymbolSpan(
        symbolSpans,
        sourceFile,
        `${dottedPrefix}.${memberName}`,
        "classes",
        member,
      );
    }
  }

  members.sort((left, right) => left.name.localeCompare(right.name));
  methods.sort((left, right) => left.name.localeCompare(right.name));
  accessors.sort((left, right) => {
    const nameOrder = left.name.localeCompare(right.name);
    return nameOrder === 0 ? left.kind.localeCompare(right.kind) : nameOrder;
  });
  innerClasses.sort((left, right) => left.name.localeCompare(right.name));

  return {
    name: expression.getName() ?? dottedPrefix.split(".").at(-1),
    members,
    methods,
    accessors,
    inner_classes: innerClasses,
  };
}

function parseClassDeclaration(declaration, sourceFile, symbolSpans) {
  const name = declaration.getName();
  addSymbolSpan(symbolSpans, sourceFile, name, "classes", declaration);
  return parseClassExpression(declaration, sourceFile, symbolSpans, name);
}

function parseReExports(sourceFile) {
  const reExports = [];
  for (const declaration of sourceFile.getExportDeclarations()) {
    const module = declaration.getModuleSpecifierValue();
    if (!module) {
      continue;
    }

    const names = declaration
      .getNamedExports()
      .map((specifier) => specifier.getAliasNode()?.getText() ?? specifier.getName())
      .sort((left, right) => left.localeCompare(right));

    reExports.push({
      module,
      names,
    });
  }
  return reExports;
}

function parseSource(filename, source) {
  const project = new Project({
    useInMemoryFileSystem: true,
    compilerOptions: {
      allowJs: false,
      target: 99,
      jsx: 4,
    },
  });

  const scriptKind = filename.endsWith(".tsx") ? ScriptKind.TSX : ScriptKind.TS;
  const sourceFile = project.createSourceFile(filename, source, {
    overwrite: true,
    scriptKind,
  });

  const symbolSpans = {};
  const interfaces = sourceFile
    .getInterfaces()
    .filter((declaration) => isExported(declaration))
    .map((declaration) =>
      parseInterfaceDeclaration(declaration, sourceFile, symbolSpans),
    );
  const typeAliases = sourceFile
    .getTypeAliases()
    .filter((declaration) => isExported(declaration))
    .map((declaration) =>
      parseTypeAliasDeclaration(declaration, sourceFile, symbolSpans),
    );
  const enums = sourceFile
    .getEnums()
    .filter((declaration) => isExported(declaration))
    .map((declaration) => parseEnumDeclaration(declaration, sourceFile, symbolSpans));
  const classes = sourceFile
    .getClasses()
    .filter((declaration) => isExported(declaration))
    .map((declaration) => parseClassDeclaration(declaration, sourceFile, symbolSpans));
  const functions = parseFunctions(sourceFile, symbolSpans);
  const globals = parseGlobals(sourceFile, symbolSpans);
  const imports = parseImports(sourceFile);
  const reExports = parseReExports(sourceFile);

  return {
    filename,
    language: "typescript",
    available_symbol_types: SYMBOL_TYPES,
    imports,
    globals,
    classes,
    functions,
    interfaces,
    type_aliases: typeAliases,
    enums,
    re_exports: reExports,
    symbol_spans: symbolSpans,
  };
}

async function main() {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }

  const input = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  const result = parseSource(input.filename, input.source);
  process.stdout.write(JSON.stringify(result));
}

main().catch((error) => {
  process.stderr.write(`${error.stack ?? error}\n`);
  process.exitCode = 1;
});
