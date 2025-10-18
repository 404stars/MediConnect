import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { SolicitarRecuperacionComponent } from './solicitar-recuperacion.component';
import { RestablecerPasswordComponent } from './restablecer-password.component';
import { NotificationModalComponent } from './shared/notification-modal/notification-modal.component';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, FormsModule, NotificationModalComponent],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  protected readonly title = signal('MediConnect');
}
