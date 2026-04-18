import { Project, Node } from "ts-morph";
import fs from "node:fs";
import path from "node:path";

function normalizePath(filePath) {
  return filePath.split(path.sep).join("/");
}

function readInput() {
  const raw = fs.readFileSync(0, "utf8");
  return JSON.parse(raw);
}

function getText(node) {
  return node.getText();
}

function getName(node) {
  if (typeof node.getName === "function") {
    return node.getName() ?? null;
  }
  return null;
}

function pushSpan(spans, symbol, symbolType, node) {
  if (!symbol) {
    return;
  }

  spans[symbol] = {
    symbol_type: symbolType,
    code: getText(node),
  };
}

function parseImport(node) {
  const defaultImport = node.getDefaultImport();
  const namespaceImport = node.getNamespaceImport();
  const namedImports = node
    .getNamedImports()
    .map((named) => named.getName())
    .sort((left, right) => left.localeCompare(right));

  return {
    module: node.getModuleSpecifierValue(),
    default: defaultImport?.getText() ?? null,
    namespace: namespaceImport?.getText() ?? null,
    named: namedImports,
  };
}

function parseVariableStatement(node, globals, spans, functions) {
  const declarationKind = node.getDeclarationKind();

  for (const declaration of node.getDeclarations()) {
    const name = declaration.getName();
    globals.push({ name, declaration_kind: declarationKind });
    pushSpan(spans, name, "globals", declaration);

    const initializer = declaration.getInitializer();
    if (initializer && Node.isArrowFunction(initializer)) {
      functions.push({ name, syntax: "arrow" });
      pushSpan(spans, name, "functions", declaration);
    }
  }
}

function parseMethod(methodNode, prefix, spans) {
  const name = getName(methodNode);
  if (!name) {
    return null;
  }

  pushSpan(spans, `${prefix}.${name}`, "classes", methodNode);
  return { name };
}

function parseAccessor(accessorNode, prefix, kind, spans) {
  const name = getName(accessorNode);
  if (!name) {
    return null;
  }

  pushSpan(spans, `${prefix}.${name}`, "classes", accessorNode);
  return { name, kind };
}

function parseProperty(propertyNode, prefix, spans, innerClasses) {
  const name = getName(propertyNode);
  if (!name) {
    return null;
  }

  pushSpan(spans, `${prefix}.${name}`, "classes", propertyNode);

  const initializer = propertyNode.getInitializer();
  if (initializer && Node.isClassExpression(initializer)) {
    const className = getName(initializer) ?? name;
    const parsedInnerClass = parseClassLike(initializer, `${prefix}.${className}`, spans, className);
    innerClasses.push(parsedInnerClass.classRecord);
    pushSpan(spans, `${prefix}.${className}`, "classes", initializer);
  }

  return { name };
}

function parseClassLike(classNode, symbolPath, spans, explicitName = null) {
  const className = explicitName ?? getName(classNode);
  const members = [];
  const methods = [];
  const accessors = [];
  const innerClasses = [];

  for (const member of classNode.getMembers()) {
    if (Node.isPropertyDeclaration(member)) {
      const property = parseProperty(member, symbolPath, spans, innerClasses);
      if (property) {
        members.push(property);
      }
      continue;
    }

    if (Node.isMethodDeclaration(member)) {
      const method = parseMethod(member, symbolPath, spans);
      if (method) {
        methods.push(method);
      }
      continue;
    }

    if (Node.isGetAccessorDeclaration(member)) {
      const accessor = parseAccessor(member, symbolPath, "getter", spans);
      if (accessor) {
        accessors.push(accessor);
      }
      continue;
    }

    if (Node.isSetAccessorDeclaration(member)) {
      const accessor = parseAccessor(member, symbolPath, "setter", spans);
      if (accessor) {
        accessors.push(accessor);
      }
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
    classRecord: {
      name: className,
      members,
      methods,
      accessors,
      inner_classes: innerClasses,
    },
  };
}

function parseReExport(node) {
  const named = node
    .getNamedExports()
    .map((specifier) => specifier.getName())
    .sort((left, right) => left.localeCompare(right));

  return {
    module: node.getModuleSpecifierValue() ?? null,
    names: named,
    export_all: node.isNamespaceExport() || named.length === 0,
  };
}

function main() {
  const input = readInput();
  const filePath = path.resolve(input.filename);
  const sourceText = fs.readFileSync(filePath, "utf8");

  const project = new Project({
    useInMemoryFileSystem: false,
    skipAddingFilesFromTsConfig: true,
    compilerOptions: {
      allowJs: false,
      target: 99,
    },
  });

  const sourceFile = project.createSourceFile(filePath, sourceText, { overwrite: true });
  const imports = [];
  const globals = [];
  const classes = [];
  const functions = [];
  const interfaces = [];
  const typeAliases = [];
  const enums = [];
  const reExports = [];
  const spans = {};

  for (const statement of sourceFile.getStatements()) {
    if (Node.isImportDeclaration(statement)) {
      imports.push(parseImport(statement));
      continue;
    }

    if (Node.isVariableStatement(statement)) {
      parseVariableStatement(statement, globals, spans, functions);
      continue;
    }

    if (Node.isFunctionDeclaration(statement)) {
      const name = getName(statement);
      if (name) {
        functions.push({ name, syntax: "function" });
        pushSpan(spans, name, "functions", statement);
      }
      continue;
    }

    if (Node.isClassDeclaration(statement)) {
      const name = getName(statement);
      if (name) {
        const parsedClass = parseClassLike(statement, name, spans);
        classes.push(parsedClass.classRecord);
        pushSpan(spans, name, "classes", statement);
      }
      continue;
    }

    if (Node.isInterfaceDeclaration(statement)) {
      const name = getName(statement);
      if (name) {
        interfaces.push({ name });
        pushSpan(spans, name, "interfaces", statement);
      }
      continue;
    }

    if (Node.isTypeAliasDeclaration(statement)) {
      const name = getName(statement);
      if (name) {
        typeAliases.push({ name });
        pushSpan(spans, name, "type_aliases", statement);
      }
      continue;
    }

    if (Node.isEnumDeclaration(statement)) {
      const name = getName(statement);
      if (name) {
        enums.push({ name });
        pushSpan(spans, name, "enums", statement);
      }
      continue;
    }

    if (Node.isExportDeclaration(statement)) {
      reExports.push(parseReExport(statement));
    }
  }

  imports.sort((left, right) => left.module.localeCompare(right.module));
  globals.sort((left, right) => left.name.localeCompare(right.name));
  classes.sort((left, right) => left.name.localeCompare(right.name));
  functions.sort((left, right) => {
    const nameOrder = left.name.localeCompare(right.name);
    return nameOrder === 0 ? left.syntax.localeCompare(right.syntax) : nameOrder;
  });
  interfaces.sort((left, right) => left.name.localeCompare(right.name));
  typeAliases.sort((left, right) => left.name.localeCompare(right.name));
  enums.sort((left, right) => left.name.localeCompare(right.name));
  reExports.sort((left, right) => {
    const leftModule = left.module ?? "";
    const rightModule = right.module ?? "";
    return leftModule.localeCompare(rightModule);
  });

  const result = {
    filename: normalizePath(path.relative(process.cwd(), filePath)),
    language: "typescript",
    available_symbol_types: [
      "imports",
      "globals",
      "classes",
      "functions",
      "interfaces",
      "type_aliases",
      "enums",
      "re_exports"
    ],
    imports,
    globals,
    classes,
    functions,
    interfaces,
    type_aliases: typeAliases,
    enums,
    re_exports: reExports,
    fetched_symbols: spans,
  };

  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}

main();
