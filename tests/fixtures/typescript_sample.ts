import Thing, { Helper } from "./types";
import * as Utils from "./utils";

export const TOP_LEVEL_CONST = 1;
export const arrowFunction = (value: string): string => value.trim();
export let mutableValue = 0;

export function namedFunction(input: number): number {
  return input + TOP_LEVEL_CONST;
}

export interface MyInterface {
  id: string;
}

export type MyType = {
  enabled: boolean;
};

export enum MyEnum {
  Ready = "ready",
}

export abstract class MyClass {
  value = 1;
  InnerClass = class InnerClass {
    runInner(): string {
      return "inner";
    }
  };

  run(): number {
    return this.value;
  }

  get label(): string {
    return String(this.value);
  }

  set label(next: string) {
    this.value = Number(next);
  }
}

export { SharedThing } from "./shared";
export * from "./everything";
