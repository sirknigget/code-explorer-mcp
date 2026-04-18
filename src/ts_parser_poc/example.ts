import Thing, { Helper } from "./types";
import * as fs from "node:fs";

export const TOP_LEVEL_CONST = 1;
export let topLevelLet = "value";
export var topLevelVar = true;

export async function namedFunction(input: string): Promise<string> {
  return input.trim();
}

export const arrowFunction = (count: number): number => count + 1;

export interface MyInterface {
  id: string;
}

export type MyType = {
  name: string;
};

export enum MyEnum {
  One = "one",
  Two = "two",
}

export abstract class MyClass {
  value = 0;

  get label(): string {
    return String(this.value);
  }

  set label(next: string) {
    this.value = Number(next);
  }

  run(): void {}

  static InnerClass = class InnerClass {
    nested = true;

    runInner(): void {}
  };
}

export { SharedThing } from "./shared";
export * from "./shared-all";
