import React from 'react';
import { createRoot } from 'react-dom/client';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import './styles/index.css';
import { RouteError } from './components/RouteError';
import Landing from './screens/Landing';
import Describe from './screens/Describe';
import Interview from './screens/Interview';
import Forge from './screens/Forge';
import Multiverse from './screens/Multiverse';
import Flips from './screens/Flips';
import Branches from './screens/Branches';
import Report from './screens/Report';

const errorElement = <RouteError />;

const router = createBrowserRouter([
  { path: '/', element: <Landing />, errorElement },
  { path: '/s/:id/describe', element: <Describe />, errorElement },
  { path: '/s/:id/interview', element: <Interview />, errorElement },
  { path: '/s/:id/forge', element: <Forge />, errorElement },
  { path: '/s/:id/multiverse', element: <Multiverse />, errorElement },
  { path: '/s/:id/flips', element: <Flips />, errorElement },
  { path: '/s/:id/branches', element: <Branches />, errorElement },
  { path: '/s/:id/report', element: <Report />, errorElement },
   { path: '*', element: <RouteError notFound /> },
]);

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
);