import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { PasswordService } from './services/password.service';
import { CommonModule } from '@angular/common';
import { Navbar } from './shared/navbar/navbar';

@Component({
  selector: 'app-solicitar-recuperacion',
  standalone: true,
  imports: [CommonModule, FormsModule, Navbar],
  providers: [PasswordService],
  templateUrl: './solicitar-recuperacion.component.html',
})
export class SolicitarRecuperacionComponent {
  email: string = '';
  mensaje: string = '';
  loading = false;

  constructor(private passwordService: PasswordService) {}

  solicitar() {
    // Validar que el correo no esté vacío
    if (!this.email || this.email.trim() === '') {
      this.mensaje = '[WARNING] Por favor ingresa tu correo electrónico.';
      return;
    }

    // Validar formato básico de email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(this.email)) {
      this.mensaje = '[WARNING] Por favor ingresa un correo electrónico válido.';
      return;
    }

    this.loading = true;
    this.mensaje = '';
    
    this.passwordService.solicitarRecuperacion(this.email).subscribe({
      next: () => {
        this.mensaje = '[SUCCESS] Si el correo está registrado, recibirás un email con instrucciones.';
        this.loading = false;
      },
      error: () => {
        this.mensaje = '[ERROR] Error al solicitar recuperación. Intenta nuevamente.';
        this.loading = false;
      }
    });
  }
}
