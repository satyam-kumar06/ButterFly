import React from 'react';
import { createRoot } from 'react-dom/client';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import './styles/index.css';
import Landing from './screens/Landing';
import Describe from './screens/Describe';
import Interview from './screens/Interview';
import Forge from './screens/Forge';
import Multiverse from './screens/Multiverse';
import Flips from './screens/Flips';
import Branches from './screens/Branches';
import Report from './screens/Report';

const router = createBrowserRouter([
  { path: '/', element: <Landing /> },
  { path: '/s/:id/describe', element: <Describe /> },
  { path: '/s/:id/interview', element: <Interview /> },
  { path: '/s/:id/forge', element: <Forge /> },
  { path: '/s/:id/multiverse', element: <Multiverse /> },
  { path: '/s/:id/flips', element: <Flips /> },
  { path: '/s/:id/branches', element: <Branches /> },
  { path: '/s/:id/report', element: <Report /> },
]);

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
);