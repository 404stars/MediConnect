import { Component, OnInit, OnDestroy } from '@angular/core';
import { RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../services/auth.service';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [RouterModule, CommonModule],
  templateUrl: './navbar.html',
  styleUrls: ['./navbar.css']
})
export class Navbar implements OnInit, OnDestroy {
  isLoggedIn = false;
  userRoles: string[] = [];
  activeRole: string | null = null;
  userName = '';
  isLoggingOut = false;
  private subscription: Subscription = new Subscription();

  constructor(private authService: AuthService, private router: Router) {}

  ngOnInit() {
    this.subscription.add(
      this.authService.currentUser$.subscribe(user => {
        this.isLoggedIn = this.authService.isLoggedIn();
        if (user) {
          this.userRoles = user.roles || [];
          this.userName = user.nombre || '';
          this.activeRole = this.authService.getActiveRole();
        } else {
          this.userRoles = [];
          this.userName = '';
          this.activeRole = null;
        }
      })
    );
  }

  ngOnDestroy() {
    this.subscription.unsubscribe();
  }

  logout() {
    this.isLoggingOut = true;
    
    this.authService.logout().subscribe({
      next: (response) => {
        console.log('Logout exitoso:', response);
        this.isLoggingOut = false;
        this.router.navigate(['/login']);
      },
      error: (error) => {
        console.error('Error en logout:', error);
        this.isLoggingOut = false;
        this.router.navigate(['/login']);
      }
    });
  }

  hasRole(role: string): boolean {
    return this.activeRole === role;
  }

  hasPermission(permission: string): boolean {
    return this.authService.hasPermission(permission);
  }
  
  cambiarRol() {
    this.authService.removeActiveRole();
    this.router.navigate(['/selector-rol']);
  }
}
