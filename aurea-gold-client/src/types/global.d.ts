declare global {
  var BASE_API: string;
  interface Window {
    BASE_API: string;
  }
}
export {};
