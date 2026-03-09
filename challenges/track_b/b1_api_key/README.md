# B1. Get a Circle API Key

Create a Circle developer account and generate an API key. No code to write, just account setup.

## Steps

1. **Create an account** on the [Circle Developer Console](https://console.circle.com)

2. **Generate an API key** from the Console dashboard

3. **Confirm access** to the Arc testnet environment in the Console

## Environment Variables

Once you have your API key, set it in your shell:

```bash
export CIRCLE_API_KEY="your-api-key"
```

You will also need an entity secret for wallet operations in later steps:

```bash
export CIRCLE_ENTITY_SECRET="your-entity-secret"
```

## Checkpoint

A working API key in the Circle Developer Console.
