/** Node Vitest stand-in for the runtime-provided cloudflare:workers base class. */
export abstract class DurableObject<RuntimeEnv = Env> {
  protected readonly ctx: DurableObjectState;
  protected readonly env: RuntimeEnv;

  constructor(ctx: DurableObjectState, env: RuntimeEnv) {
    this.ctx = ctx;
    this.env = env;
  }
}
