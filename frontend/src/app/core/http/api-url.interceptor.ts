import { HttpInterceptorFn } from '@angular/common/http';

const PRODUCTION_API_ORIGIN =
  'https://msme-credit-intelligence.onrender.com';

export const apiUrlInterceptor: HttpInterceptorFn = (
  request,
  next
) => {
  const isLocalDevelopment =
    window.location.hostname === 'localhost' ||
    window.location.hostname === '127.0.0.1';

  const isRelativeApiRequest =
    request.url.startsWith('/api/');

  if (isLocalDevelopment || !isRelativeApiRequest) {
    return next(request);
  }

  const productionRequest = request.clone({
    url: `${PRODUCTION_API_ORIGIN}${request.url}`,
  });

  return next(productionRequest);
};