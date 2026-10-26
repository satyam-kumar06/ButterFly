import { Link, isRouteErrorResponse, useRouteError } from 'react-router-dom';

export function RouteError({ notFound: forceNotFound = false }: { notFound?: boolean }) {
  const error = useRouteError();
  const notFound = forceNotFound || (isRouteErrorResponse(error) && error.status === 404);
  return (
    <main className="mx-auto max-w-xl p-8">
      <h1 className="font-display text-4xl font-semibold">
        {notFound ? 'Page not found' : 'Something went wrong'}
      </h1>
      <p className="mt-2 text-muted">
        {notFound ? 'That page does not exist.' : 'This screen failed to load. Going home usually fixes it.'}
      </p>
      <Link to="/" className="glass mt-6 inline-block px-5 py-3">Go home</Link>
    </main>
  );
}