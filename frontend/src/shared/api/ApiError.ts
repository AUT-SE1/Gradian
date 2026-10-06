export class ApiError extends Error {
  constructor(public readonly status: number, public readonly payload: unknown) {
    super(`API request failed with status ${status}`);
    this.name = 'ApiError';
  }
}
