import { Injectable } from '@angular/core';
import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError } from 'rxjs/operators';
import { throwError } from 'rxjs';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  
  const token = localStorage.getItem('auth_token');
  
  let cloned = req;
  
  if (token) {
    cloned = req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    });
  }
  
  return next(cloned).pipe(
    catchError((error: HttpErrorResponse) => {
      const isLoginRequest = req.url.includes('/auth/login') || req.url.includes('/auth/register');
      const isPasswordRecovery = req.url.includes('/recuperar-password') || req.url.includes('/restablecer-password');
      const hasToken = !!token;
      const isTokenError = error.error?.detail?.includes('Token inválido') ||
                          error.error?.detail?.includes('Token expirado') ||
                          error.error?.detail?.includes('Not authenticated');
      
      // Solo manejar sesión expirada si:
      // 1. NO es login/registro
      // 2. NO es recuperación de contraseña  
      // 3. SÍ había un token (estaba logueado)
      // 4. Es error de token
      if (!isLoginRequest && 
          !isPasswordRecovery &&
          hasToken &&
          (error.status === 401 || error.status === 403) &&
          isTokenError) {
        
        console.warn('Token expirado o inválido. Cerrando sesión...');
        
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
        localStorage.removeItem('active_role');
        localStorage.removeItem('user_roles');
        localStorage.removeItem('additional_info');
        
        router.navigate(['/login']);
        
        setTimeout(() => {
          alert('Su sesión ha expirado. Por favor, inicie sesión nuevamente.');
        }, 100);
      }
      
      return throwError(() => error);
    })
  );
};
