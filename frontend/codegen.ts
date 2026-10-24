import type { CodegenConfig } from "@graphql-codegen/cli";
const config: CodegenConfig = {
  schema: "../contracts/schema.graphql",
  documents: ["src/**/*.graphql"],
  generates: {
    "src/gql/": {
      preset: "client",
      config: {
        strictScalars: true,
        scalars: {
          Date: { input: "string", output: "string" },
          UUID: { input: "string", output: "string" },
        },
        useTypeImports: true,
        immutableTypes: true,
        enumsAsTypes: true,
        avoidOptionals: { field: true, inputValue: false },
      },
    },
  },
};
export default config;
