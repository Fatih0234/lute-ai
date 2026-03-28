# Lute v3 + AI Explanation (Fork)

[![tests](https://github.com/jzohrab/lute_v3/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/jzohrab/lute_v3/actions/workflows/ci.yml?query=branch%3Amaster)
[![code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![linting: pylint](https://img.shields.io/badge/linting-pylint-yellowgreen)](https://github.com/pylint-dev/pylint)
[![coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/jzohrab/a15001ec2ff889f7be0b553df9881566/raw/covbadge.json)](https://github.com/jzohrab/lute_v3/actions/workflows/ci.yml?query=branch%3Amaster)
[![Discord Server](https://badgen.net/badge/icon/discord?icon=discord&label)](https://discord.gg/CzFUQP5m8u)


This repo contains the source code for Lute (Learning Using Texts) v3, a Python/Flask tool for learning foreign languages through reading.

To learn more about Lute v3, or to install it for your own use and study, please see the [Lute v3 manual](https://luteorg.github.io/lute-manual/).

![Lute v3 demo](https://luteorg.github.io/lute-manual/assets/intro.gif)

# AI Explanation Feature (Add-on)

This fork includes an **AI-powered text explanation** feature that helps language learners understand difficult text passages. When reading, click the new "AI Explain" tab to get:

- **Short Translation** - Quick translation to your target language
- **Literal Gloss** - Word-by-word breakdown  
- **Meaning in Context** - Contextual explanation
- **Grammar Notes** - Key grammar points identified
- **Alternatives** - Alternative phrasings
- **Usage Notes** - Cultural and usage information

### Setup

1. Get a MiniMax API key from https://www.minimaxi.com/
2. Set the environment variable:
   ```bash
   export ANTHROPIC_API_KEY=your_minimax_api_key_here
   ```

3. Start Lute and the AI Explain tab will appear in the reading interface

See the full [AI Explanation documentation](./lute/ai_explain/README.md) for configuration options, API usage, and troubleshooting.

# Getting Started

## Users

See the [Lute v3 manual](https://luteorg.github.io/lute-manual/).  Hop onto the [Discord](https://discord.gg/CzFUQP5m8u) too.

## Developing

### Quick Start

1. Clone the repository with submodules:
   ```bash
   git clone --recurse-submodules https://github.com/Fatih0234/lute-ai.git
   ```
   
   Or if you've already cloned without submodules:
   ```bash
   git submodule update --init --recursive
   ```
   
   **Note:** The `lute/db/language_defs` directory is a Git submodule that contains predefined language definitions. Without initializing it, the application will fail to start with a "Missing language def" error.

2. Set up your development environment and install dependencies.

For more information on building and developing, please see [Development](../../wiki/Development).

## Contributing

If you'd like to contribute code to Lute (hooray!), check out the [Contribution Guidelines](../../wiki/Contributing).  And with every repo star, an angel gets its wings.

# License

Lute uses the MIT license: [LICENSE](./LICENSE.txt)
