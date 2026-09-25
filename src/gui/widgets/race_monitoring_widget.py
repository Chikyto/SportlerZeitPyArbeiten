from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QGroupBox, QTableWidget, QTableWidgetItem,
                            QHeaderView, QComboBox, QTabWidget, QTextEdit,
                            QMenu, QDialog, QTimeEdit, QDialogButtonBox, QFormLayout,
                            QMessageBox)
from PyQt6.QtCore import pyqtSignal, QTimer, Qt, QTime
from PyQt6.QtGui import QFont, QColor
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class RaceMonitoringWidget(QWidget):
    """Widget para monitoreo de carreras en tiempo real"""

    # Señales
    refresh_requested = pyqtSignal()

    def __init__(self, race_manager=None):
        super().__init__()
        self.race_manager = race_manager
        self.setup_ui()

        if race_manager:
            self.refresh_category_combo()

        # Timer para actualización automática
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_all_data)
        self.refresh_timer.start(2000)  # Actualizar cada 2 segundos
        
    def setup_ui(self):
        """Configurar interfaz del widget"""
        layout = QVBoxLayout(self)
        
        # Controles superiores
        controls_group = QGroupBox("Control de Monitoreo")
        controls_layout = QHBoxLayout(controls_group)
        
        # Selector de categoría
        controls_layout.addWidget(QLabel("Distancia:"))
        self.category_combo = QComboBox()
        self.category_combo.addItem("Todas las categorías")
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        controls_layout.addWidget(self.category_combo)
        
        # Botones de control
        self.refresh_btn = QPushButton("Actualizar")
        self.refresh_btn.clicked.connect(self.refresh_all_data)
        controls_layout.addWidget(self.refresh_btn)
        
        self.auto_refresh_btn = QPushButton("Auto: ON")
        self.auto_refresh_btn.clicked.connect(self.toggle_auto_refresh)
        self.auto_refresh_btn.setStyleSheet("background-color: green; color: white;")
        controls_layout.addWidget(self.auto_refresh_btn)

        # Botón de exportación
        self.export_btn = QPushButton("📊 Exportar Resultados")
        self.export_btn.clicked.connect(self.show_export_dialog)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
                padding: 8px 15px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover { background: #2563eb; }
        """)
        controls_layout.addWidget(self.export_btn)

        # Botón de largada masiva
        self.bulk_start_btn = QPushButton("🏁 Asignar Largada Masiva")
        self.bulk_start_btn.clicked.connect(self._bulk_assign_start_time)
        self.bulk_start_btn.setStyleSheet("""
            QPushButton {
                background: #f59e0b;
                color: white;
                padding: 8px 15px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover { background: #d97706; }
        """)
        self.bulk_start_btn.setEnabled(False)
        self.bulk_start_btn.setToolTip(
            "Seleccioná una distancia y asegurate de que la carrera\n"
            "esté iniciada para habilitar esta función."
        )
        controls_layout.addWidget(self.bulk_start_btn)

        controls_layout.addStretch()
        
        # Estado del sistema
        self.system_status_label = QLabel("Sistema: Desconectado")
        self.system_status_label.setStyleSheet("font-weight: bold;")
        controls_layout.addWidget(self.system_status_label)
        
        layout.addWidget(controls_group)
        
        # Pestañas para diferentes vistas
        self.monitoring_tabs = QTabWidget()
        
        # Tab 1: Resumen de categorías
        self.setup_categories_overview_tab()
        
        # Tab 2: Participantes en tiempo real
        self.setup_participants_tab()
        
        # Tab 3: Estadísticas detalladas
        self.setup_statistics_tab()

        # Tab 4: Podios por categoría de premiación
        self.setup_podiums_tab()

        # Tab 5: Tiempos parciales (Splits)
        self.setup_splits_tab()

        layout.addWidget(self.monitoring_tabs)
        
    def setup_categories_overview_tab(self):
        """Tab con resumen de todas las categorías"""
        tab = QWidget()
        self.monitoring_tabs.addTab(tab, "Resumen de Distancias")
        
        layout = QVBoxLayout(tab)
        
        # Tabla de categorías con estado
        self.categories_overview_table = QTableWidget()
        self.categories_overview_table.setColumnCount(8)
        self.categories_overview_table.setHorizontalHeaderLabels([
            "Distancia", "Estado", "Hora Inicio", "Participantes",
            "No Iniciados", "En Carrera", "Finalizados", "Último Checkpoint"
        ])
        
        # Configurar tabla
        header = self.categories_overview_table.horizontalHeader()
        header.setStretchLastSection(True)
        for i in range(7):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        self.categories_overview_table.setAlternatingRowColors(True)
        layout.addWidget(self.categories_overview_table)
        
    def setup_participants_tab(self):
        """Tab con participantes en tiempo real"""
        tab = QWidget()
        self.monitoring_tabs.addTab(tab, "Participantes")
        
        layout = QVBoxLayout(tab)
        
        # Filtros
        filters_layout = QHBoxLayout()
        
        filters_layout.addWidget(QLabel("Mostrar:"))
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems([
            "Todos", "No iniciados", "En carrera", "Finalizados"
        ])
        self.status_filter_combo.currentTextChanged.connect(self.refresh_participants_table)
        filters_layout.addWidget(self.status_filter_combo)
        
        filters_layout.addStretch()
        
        # Contadores
        self.participants_count_label = QLabel("Total: 0 participantes")
        self.participants_count_label.setStyleSheet("font-weight: bold;")
        filters_layout.addWidget(self.participants_count_label)
        
        layout.addLayout(filters_layout)
        
        # Tabla de participantes
        self.participants_table = QTableWidget()
        self.participants_table.setColumnCount(8)
        self.participants_table.setHorizontalHeaderLabels([
            "Chip", "Distancia", "Estado", "Tiempo Inicio",
            "Tiempo Actual", "Checkpoints", "Última Lectura", "Antena"
        ])
        
        # Configurar tabla
        header = self.participants_table.horizontalHeader()
        header.setStretchLastSection(True)
        for i in range(7):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        self.participants_table.setAlternatingRowColors(True)
        self.participants_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.participants_table.customContextMenuRequested.connect(self._participants_context_menu)
        layout.addWidget(self.participants_table)

    def _participants_context_menu(self, pos):
        """Context menu para tabla de participantes"""
        row = self.participants_table.rowAt(pos.y())
        if row < 0:
            return
        menu = QMenu(self)
        correct_times_action = menu.addAction("⏱ Corregir Tiempos (Largada / Llegada)")
        menu.addSeparator()
        dns_action = menu.addAction("🚫 DNS — No tomó la salida")
        dnf_action = menu.addAction("🛑 DNF — Abandonó la carrera")
        dsq_action = menu.addAction("❌ DSQ — Descalificado")
        action = menu.exec(self.participants_table.viewport().mapToGlobal(pos))
        if action == correct_times_action:
            self._correct_times(row)
        elif action == dns_action:
            self._set_athlete_status(row, 'dns')
        elif action == dnf_action:
            self._set_athlete_status(row, 'dnf')
        elif action == dsq_action:
            self._set_athlete_status(row, 'dsq')

    def _correct_times(self, row):
        """Diálogo para corregir/reasignar tiempos de largada y llegada."""
        if not self.race_manager:
            return

        tag_id = self.participants_table.item(row, 0).text()
        distance_id = self.participants_table.item(row, 1).text()

        results = self.race_manager.get_results(distance_id)
        result = next((r for r in results if r.athlete.tag_id == tag_id), None)
        if result is None:
            QMessageBox.warning(self, "Error", "No se encontró el atleta en la distancia.")
            return

        category = self.race_manager.get_category(distance_id)
        athlete_name = result.athlete.name if hasattr(result.athlete, 'name') else tag_id

        from datetime import datetime, date
        ref_date = category.start_time.date() if (category and category.start_time) else date.today()
        gun_dt = category.start_time if (category and category.start_time) else None

        def _to_qtime(dt):
            return QTime(dt.hour, dt.minute, dt.second) if dt else QTime(0, 0, 0)

        gun_qtime = _to_qtime(gun_dt)
        has_start  = result.start_time is not None
        has_finish = result.finish_time is not None

        # ── Detectar el caso "solo una lectura, puede estar mal asignada" ──────
        only_start  = has_start and not has_finish
        only_finish = has_finish and not has_start
        neither     = not has_start and not has_finish

        dlg = QDialog(self)
        dlg.setWindowTitle("Corrección de Tiempos")
        dlg.setMinimumWidth(400)
        layout = QVBoxLayout(dlg)

        # Encabezado
        layout.addWidget(QLabel(f"<b>{athlete_name}</b> — {distance_id}"))

        # Estado actual visible
        gun_str   = gun_dt.strftime('%H:%M:%S') if gun_dt else '—'
        start_str = result.start_time.strftime('%H:%M:%S') if has_start else '—'
        finish_str= result.finish_time.strftime('%H:%M:%S') if has_finish else '—'
        info = QLabel(
            f"<small>Disparo distancia: <b>{gun_str}</b> &nbsp;|&nbsp; "
            f"Largada registrada: <b>{start_str}</b> &nbsp;|&nbsp; "
            f"Llegada registrada: <b>{finish_str}</b></small>"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # ── Atajo rápido: solo hay un tiempo y probablemente está mal asignado ─
        if only_start:
            # Hay solo largada — puede ser que ese tiempo sea en realidad la llegada
            misread_btn = QPushButton(
                f"↩ Reasignar: mover largada ({start_str}) → llegada  +  largada = disparo ({gun_str})"
            )
            misread_btn.setStyleSheet("background:#f0a500; color:white; font-weight:bold; padding:6px;")
            misread_btn.setToolTip(
                "Usa el tiempo ya registrado como llegada y asigna la hora de disparo como largada"
            )

            def _reassign_start_to_finish():
                recorded = result.start_time
                # Asignar hora de disparo como largada
                new_start = gun_dt or recorded
                result.record_start(new_start)
                # Mover el tiempo original a llegada
                result.record_finish(recorded)
                logger.info(f"Reasignación: {athlete_name} largada={new_start.strftime('%H:%M:%S')} llegada={recorded.strftime('%H:%M:%S')}")
                self._backend_send(tag_id, distance_id, 'start', new_start)
                self._backend_send(tag_id, distance_id, 'finish', recorded)
                self.refresh_participants_table()
                dlg.accept()
                QMessageBox.information(
                    self, "Tiempos reasignados",
                    f"<b>{athlete_name}</b><br>"
                    f"Largada: {new_start.strftime('%H:%M:%S')}<br>"
                    f"Llegada: {recorded.strftime('%H:%M:%S')}"
                )

            misread_btn.clicked.connect(_reassign_start_to_finish)
            layout.addWidget(misread_btn)

        elif only_finish:
            # Hay solo llegada — ofrecer asignar la hora de disparo como largada
            misread_btn = QPushButton(
                f"↩ Asignar largada = disparo ({gun_str})  (llegada {finish_str} queda igual)"
            )
            misread_btn.setStyleSheet("background:#f0a500; color:white; font-weight:bold; padding:6px;")

            def _assign_gun_as_start():
                new_start = gun_dt or result.finish_time
                result.record_start(new_start)
                logger.info(f"Largada manual (disparo): {athlete_name} @ {new_start.strftime('%H:%M:%S')}")
                self._backend_send(tag_id, distance_id, 'start', new_start)
                self.refresh_participants_table()
                dlg.accept()
                QMessageBox.information(
                    self, "Largada asignada",
                    f"<b>{athlete_name}</b><br>Largada: {new_start.strftime('%H:%M:%S')}<br>Llegada: {finish_str}"
                )

            misread_btn.clicked.connect(_assign_gun_as_start)
            layout.addWidget(misread_btn)

        # ── Separador ──────────────────────────────────────────────────────────
        line = QLabel("<hr>")
        line.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(line)
        layout.addWidget(QLabel("<small>O bien corrija los tiempos manualmente:</small>"))

        # ── Campos manuales ────────────────────────────────────────────────────
        form = QFormLayout()

        chk_start = QPushButton("Corregir largada")
        chk_start.setCheckable(True)
        chk_start.setChecked(neither or only_finish)
        start_edit = QTimeEdit(_to_qtime(result.start_time) if has_start else gun_qtime)
        start_edit.setDisplayFormat("HH:mm:ss")
        start_edit.setWrapping(True)
        start_edit.setEnabled(chk_start.isChecked())
        chk_start.toggled.connect(start_edit.setEnabled)
        form.addRow(chk_start, start_edit)

        chk_finish = QPushButton("Corregir llegada")
        chk_finish.setCheckable(True)
        chk_finish.setChecked(neither or only_start)
        finish_edit = QTimeEdit(_to_qtime(result.finish_time) if has_finish else QTime(0, 0, 0))
        finish_edit.setDisplayFormat("HH:mm:ss")
        finish_edit.setWrapping(True)
        finish_edit.setEnabled(chk_finish.isChecked())
        chk_finish.toggled.connect(finish_edit.setEnabled)
        form.addRow(chk_finish, finish_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        changed = []

        if chk_start.isChecked():
            qt = start_edit.time()
            new_start = datetime(ref_date.year, ref_date.month, ref_date.day,
                                 qt.hour(), qt.minute(), qt.second())
            result.record_start(new_start)
            changed.append(f"Largada: {new_start.strftime('%H:%M:%S')}")
            logger.info(f"Corrección manual largada: {athlete_name} ({tag_id}) @ {new_start.strftime('%H:%M:%S')}")
            self._backend_send(tag_id, distance_id, 'start', new_start)

        if chk_finish.isChecked():
            qt = finish_edit.time()
            new_finish = datetime(ref_date.year, ref_date.month, ref_date.day,
                                  qt.hour(), qt.minute(), qt.second())
            result.record_finish(new_finish)
            changed.append(f"Llegada: {new_finish.strftime('%H:%M:%S')}")
            logger.info(f"Corrección manual llegada: {athlete_name} ({tag_id}) @ {new_finish.strftime('%H:%M:%S')}")
            self._backend_send(tag_id, distance_id, 'finish', new_finish)

        self.refresh_participants_table()
        if changed:
            QMessageBox.information(
                self, "Tiempos corregidos",
                f"<b>{athlete_name}</b><br>" + "<br>".join(changed)
            )

    def _set_athlete_status(self, row: int, status: str):
        """Marcar un atleta como DNS / DNF / DSQ y notificar al backend."""
        if not self.race_manager:
            return

        tag_id = self.participants_table.item(row, 0).text() if self.participants_table.item(row, 0) else None
        distance_id = self.participants_table.item(row, 1).text() if self.participants_table.item(row, 1) else None
        if not tag_id or not distance_id:
            return

        labels = {'dns': 'DNS (No tomó la salida)', 'dnf': 'DNF (Abandonó)', 'dsq': 'DSQ (Descalificado)'}
        label = labels.get(status, status.upper())

        from PyQt6.QtWidgets import QMessageBox
        athlete_name = self.participants_table.item(row, 2).text() if self.participants_table.item(row, 2) else tag_id
        reply = QMessageBox.question(
            self, f"Confirmar {status.upper()}",
            f"¿Marcar a <b>{athlete_name}</b> como <b>{label}</b>?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Actualizar estado local en el modelo
        from src.core.race_tracking.models import AthleteStatus
        status_map = {
            'dns': AthleteStatus.DNS,
            'dnf': AthleteStatus.DNF,
            'dsq': AthleteStatus.DSQ,
        }
        dist = self.race_manager.get_distance(distance_id)
        if dist:
            new_status = status_map.get(status)
            for athlete in dist.participants:
                if athlete.tag_id == tag_id:
                    if new_status:
                        athlete.status = new_status
                    break

        # Enviar al backend
        self._backend_send_status(tag_id, distance_id, status)

        # Refrescar tabla
        self.refresh_data()

    def _backend_send_status(self, tag_id: str, distance_id: str, status: str):
        """Envía un evento de estado (dns/dnf/dsq) al backend."""
        try:
            from datetime import datetime
            main_window = self.window()
            if not hasattr(main_window, 'cloud_config') or not main_window.cloud_config:
                return
            import requests, threading
            cfg = main_window.cloud_config
            base_url = cfg['api_url'].rstrip('/').removesuffix('/api/v1')
            event_id = cfg.get('event_id', '')
            url = f"{base_url}/api/events/{event_id}/detection"
            headers = {'Authorization': f"Bearer {cfg['token']}"}

            # Buscar datos del atleta para incluir en el payload
            athlete_name, bib_number = None, None
            if hasattr(main_window, 'race_manager') and main_window.race_manager:
                dist = main_window.race_manager.get_distance(distance_id)
                if dist:
                    for a in dist.participants:
                        if a.tag_id == tag_id:
                            athlete_name = a.name
                            bib_number = a.bib_number
                            break

            payload = {
                'tag_id': tag_id,
                'timestamp': datetime.now().isoformat(),
                'antenna_port': 0,
                'event_type': status,          # "dns" | "dnf" | "dsq"
                'checkpoint_number': None,
                'checkpoint_km': None,
                'category_id': distance_id,
                'athlete_name': athlete_name,
                'bib_number': bib_number,
                'manual': True,
            }

            persistence = getattr(main_window, 'race_persistence', None)
            worker = getattr(main_window, 'sync_worker', None)
            if persistence and worker:
                import uuid
                payload['event_id'] = str(uuid.uuid4())
                persistence.enqueue_sync('detection', url, payload, headers)
                worker.notify()
            else:
                def _post():
                    try:
                        r = requests.post(url, json=payload, headers=headers, timeout=5)
                        if r.status_code not in (200, 201):
                            import logging
                            logging.getLogger(__name__).warning(
                                f"⚠️ Backend {status.upper()} respondió {r.status_code}: {r.text[:200]}")
                    except Exception as e:
                        import logging
                        logging.getLogger(__name__).warning(f"⚠️ No se pudo enviar {status.upper()}: {e}")
                threading.Thread(target=_post, daemon=True).start()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"⚠️ _backend_send_status falló: {e}")

    def _backend_send(self, tag_id, distance_id, role, timestamp):
        """Envía una corrección manual al backend (best-effort)."""
        try:
            main_window = self.window()
            if hasattr(main_window, '_send_detection_to_backend'):
                main_window._send_detection_to_backend({
                    'tag_id': tag_id,
                    'role': role,
                    'timestamp': timestamp,
                    'antenna': 0,
                    'distance_id': distance_id,
                    'manual_correction': True,
                })
        except Exception:
            pass

    def _bulk_assign_start_time(self):
        """Asigna el tiempo de disparo a todos los atletas sin largada registrada."""
        if not self.race_manager:
            return

        # Determinar distancia seleccionada
        selected_text = self.category_combo.currentText()
        if selected_text == "Todas las categorías":
            QMessageBox.information(
                self,
                "Seleccionar distancia",
                "Seleccioná una distancia específica para usar esta función."
            )
            return

        distance_id = selected_text.split(" - ")[0]
        category = self.race_manager.get_category(distance_id)
        if not category or not category.start_time:
            QMessageBox.warning(
                self,
                "Sin tiempo de disparo",
                "La distancia seleccionada no tiene un tiempo de disparo registrado.\n\n"
                "Iniciá la carrera primero para que quede registrado el tiempo de disparo."
            )
            return

        gun_time = category.start_time
        all_results = self.race_manager.get_results(distance_id)

        # Filtrar atletas sin largada
        without_start = [r for r in all_results if r.start_time is None]

        if not without_start:
            QMessageBox.information(
                self,
                "Todos con largada",
                "Todos los atletas de esta distancia ya tienen una largada registrada."
            )
            return

        gun_str = gun_time.strftime('%H:%M:%S')
        reply = QMessageBox.question(
            self,
            "Asignar Largada Masiva",
            f"{len(without_start)} atletas sin largada.\n\n"
            f"¿Asignar tiempo de disparo ({gun_str}) a todos?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        for result in without_start:
            result.record_start(gun_time)
            self._backend_send(result.athlete.tag_id, distance_id, 'start', gun_time)

        self.refresh_participants_table()
        logger.info(
            f"🏁 Largada masiva: {len(without_start)} atletas en {distance_id} → {gun_str}"
        )

    def setup_statistics_tab(self):
        """Tab con estadísticas detalladas"""
        tab = QWidget()
        self.monitoring_tabs.addTab(tab, "Estadísticas")
        
        layout = QVBoxLayout(tab)
        
        # Estadísticas generales
        stats_group = QGroupBox("Estadísticas en Tiempo Real")
        stats_layout = QVBoxLayout(stats_group)
        
        self.statistics_text = QTextEdit()
        self.statistics_text.setReadOnly(True)
        self.statistics_text.setMaximumHeight(200)
        stats_layout.addWidget(self.statistics_text)
        
        layout.addWidget(stats_group)
        
        # Log de eventos recientes
        events_group = QGroupBox("Eventos Recientes")
        events_layout = QVBoxLayout(events_group)
        
        self.events_log = QTextEdit()
        self.events_log.setReadOnly(True)
        self.events_log.setStyleSheet("font-family: 'Courier New'; font-size: 9pt;")
        events_layout.addWidget(self.events_log)
        
        layout.addWidget(events_group)

    def setup_podiums_tab(self):
        """Tab con podios por categoría de premiación"""
        tab = QWidget()
        self.monitoring_tabs.addTab(tab, "🏆 Podios por Distancia")

        layout = QVBoxLayout(tab)

        # Controles
        controls_layout = QHBoxLayout()

        controls_layout.addWidget(QLabel("Distancia:"))
        self.podiums_category_combo = QComboBox()
        self.podiums_category_combo.addItem("Selecciona una distancia")
        self.podiums_category_combo.currentTextChanged.connect(self.refresh_podiums)
        controls_layout.addWidget(self.podiums_category_combo)

        controls_layout.addWidget(QLabel("Top:"))
        self.podium_top_n_combo = QComboBox()
        self.podium_top_n_combo.addItems(["3", "5", "10"])
        self.podium_top_n_combo.currentTextChanged.connect(self.refresh_podiums)
        controls_layout.addWidget(self.podium_top_n_combo)

        refresh_podiums_btn = QPushButton("🔄 Actualizar Podios")
        refresh_podiums_btn.clicked.connect(self.refresh_podiums)
        controls_layout.addWidget(refresh_podiums_btn)

        export_podiums_btn = QPushButton("📄 CSV")
        export_podiums_btn.clicked.connect(self.export_podiums_to_csv)
        export_podiums_btn.setStyleSheet("background-color: #10b981; color: white; font-weight: bold;")
        export_podiums_btn.setToolTip("Exportar podios a CSV (distancia seleccionada o todas)")
        controls_layout.addWidget(export_podiums_btn)

        # Botones de exportación a PDF
        export_pdf_complete_btn = QPushButton("📄 PDF Completo")
        export_pdf_complete_btn.clicked.connect(self.export_pdf_complete)
        export_pdf_complete_btn.setStyleSheet("background-color: #e94560; color: white; font-weight: bold;")
        export_pdf_complete_btn.setToolTip("Exportar PDF completo: orden de llegada + clasificaciones por género + clasificaciones por categoría")
        controls_layout.addWidget(export_pdf_complete_btn)

        export_pdf_announcer_btn = QPushButton("🎤 PDF Relator")
        export_pdf_announcer_btn.clicked.connect(self.export_pdf_announcer)
        export_pdf_announcer_btn.setStyleSheet("background-color: #f0a500; color: white; font-weight: bold;")
        export_pdf_announcer_btn.setToolTip("Exportar formato para relator (letra grande)")
        controls_layout.addWidget(export_pdf_announcer_btn)

        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # Área de podios (scroll area con contenido dinámico)
        from PyQt6.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        self.podiums_container = QWidget()
        self.podiums_layout = QVBoxLayout(self.podiums_container)
        self.podiums_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll_area.setWidget(self.podiums_container)
        layout.addWidget(scroll_area)

        # Información inicial
        info_label = QLabel("Selecciona una distancia para ver los podios clasificados por categoría de premiación (género/edad).")
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 20px;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.podiums_layout.addWidget(info_label)

    def setup_splits_tab(self):
        """Tab con tiempos parciales (splits) detallados"""
        tab = QWidget()
        self.monitoring_tabs.addTab(tab, "⏱️ Tiempos Parciales")

        layout = QVBoxLayout(tab)

        # Controles
        controls_layout = QHBoxLayout()

        controls_layout.addWidget(QLabel("Distancia:"))
        self.splits_category_combo = QComboBox()
        self.splits_category_combo.addItem("Selecciona una distancia")
        self.splits_category_combo.currentTextChanged.connect(self.refresh_splits)
        controls_layout.addWidget(self.splits_category_combo)

        refresh_splits_btn = QPushButton("🔄 Actualizar")
        refresh_splits_btn.clicked.connect(self.refresh_splits)
        controls_layout.addWidget(refresh_splits_btn)

        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # Tabla de splits
        self.splits_table = QTableWidget()
        self.splits_table.setAlternatingRowColors(True)
        self.splits_table.setSortingEnabled(True)

        # Configurar tabla
        header = self.splits_table.horizontalHeader()
        header.setStretchLastSection(True)

        layout.addWidget(self.splits_table)

        # Información inicial
        info_label = QLabel(
            "Selecciona una distancia para ver los tiempos parciales (splits) de cada checkpoint.\n\n"
            "Los splits muestran el tiempo transcurrido en cada segmento de la carrera."
        )
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 20px;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

    def refresh_splits(self):
        """Actualizar visualización de splits"""
        import logging
        logger = logging.getLogger(__name__)

        logger.debug("🔄 Actualizando splits...")

        if not self.race_manager:
            return

        # Obtener distancia seleccionada
        selected_text = self.splits_category_combo.currentText()

        if not selected_text or selected_text == "Selecciona una distancia":
            return

        # Extraer distance_id
        distance_id = selected_text.split(" - ")[0]
        if not distance_id:
            return

        # Obtener distancia
        distance = self.race_manager.get_distance(distance_id)
        if not distance:
            logger.debug(f"  Distancia {distance_id!r} no encontrada")
            return

        # Verificar si hay checkpoints
        if distance.expected_checkpoints == 0:
            self.splits_table.setRowCount(1)
            self.splits_table.setColumnCount(1)
            self.splits_table.setHorizontalHeaderLabels(["⚠️ Información"])

            info_item = QTableWidgetItem(
                "Esta distancia no tiene checkpoints configurados.\n\n"
                "Para ver splits, ve a 'Gestión de Eventos' y configura\n"
                "el número de checkpoints para esta distancia."
            )
            info_item.setForeground(QColor(200, 100, 0))  # Naranja
            info_item.setFont(QFont("Arial", 10))
            self.splits_table.setItem(0, 0, info_item)

            # Ajustar altura de fila para mostrar mensaje completo
            self.splits_table.setRowHeight(0, 100)

            logger.info(f"  ⚠️  Distancia '{distance.name}' no tiene checkpoints configurados")
            return

        # Obtener resultados
        results = self.race_manager.get_results(distance_id)

        if not results:
            self.splits_table.setRowCount(0)
            return

        # Configurar columnas dinámicamente según número de checkpoints
        num_checkpoints = distance.expected_checkpoints
        columns = ["Pos", "Dorsal", "Nombre"]

        # Agregar columnas de splits
        for i in range(1, num_checkpoints + 1):
            columns.append(f"Split CP{i}")

        columns.append("Tiempo Final")

        self.splits_table.setColumnCount(len(columns))
        self.splits_table.setHorizontalHeaderLabels(columns)

        # Llenar tabla
        self.splits_table.setRowCount(len(results))

        for row_idx, result in enumerate(results):
            athlete = result.athlete

            # Posición
            pos_item = QTableWidgetItem(str(result.position or "-"))
            pos_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.splits_table.setItem(row_idx, 0, pos_item)

            # Dorsal
            bib_item = QTableWidgetItem(str(athlete.bib_number or "-"))
            bib_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.splits_table.setItem(row_idx, 1, bib_item)

            # Nombre
            self.splits_table.setItem(row_idx, 2, QTableWidgetItem(athlete.name))

            # Splits
            col = 3
            for i in range(1, num_checkpoints + 1):
                if i in result.splits:
                    split = result.splits[i]
                    hours = int(split.total_seconds() // 3600)
                    minutes = int((split.total_seconds() % 3600) // 60)
                    seconds = int(split.total_seconds() % 60)
                    split_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

                    split_item = QTableWidgetItem(split_text)
                    split_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                    # Colorear según velocidad (opcional)
                    # Verde para splits rápidos, amarillo normal, rojo lentos
                    split_item.setForeground(QColor(0, 100, 0))  # Verde por defecto

                    self.splits_table.setItem(row_idx, col, split_item)
                else:
                    not_passed_item = QTableWidgetItem("-")
                    not_passed_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    not_passed_item.setForeground(QColor(150, 150, 150))  # Gris
                    self.splits_table.setItem(row_idx, col, not_passed_item)

                col += 1

            # Tiempo final
            final_time_item = QTableWidgetItem(
                result.get_formatted_time() if result.finish_time else "-"
            )
            final_time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            if result.finish_time:
                final_time_item.setForeground(QColor(0, 0, 200))  # Azul
                final_time_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))

            self.splits_table.setItem(row_idx, col, final_time_item)

        # Ajustar tamaño de columnas
        header = self.splits_table.horizontalHeader()
        for i in range(len(columns)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        logger.debug(f"✅ Splits actualizados: {len(results)} atletas, {num_checkpoints} checkpoints")

    def refresh_podiums(self):
        """Actualizar visualización de podios"""
        import logging
        logger = logging.getLogger(__name__)

        logger.debug("🔄 Actualizando podios...")

        if not self.race_manager:
            return

        # Limpiar layout actual
        while self.podiums_layout.count():
            item = self.podiums_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Obtener categoría seleccionada
        selected_text = self.podiums_category_combo.currentText()
        logger.debug(f"  Distancia seleccionada: {selected_text}")

        if selected_text == "Todas las distancias":
            info_label = QLabel("Selecciona una distancia específica para ver los podios.\nUsa los botones de exportación para obtener resultados de todas las distancias.")
            info_label.setStyleSheet("color: #666; font-style: italic; padding: 20px;")
            info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            info_label.setWordWrap(True)
            self.podiums_layout.addWidget(info_label)
            return

        race_category_id = selected_text.split(" - ")[0]

        # Obtener top_n
        top_n = int(self.podium_top_n_combo.currentText())

        # Obtener podios
        try:
            logger.debug(f"  Obteniendo podios para {race_category_id} (top {top_n})...")

            # ========== 1. GENERALES POR GÉNERO (SIN CATEGORÍA DE EDAD) ==========
            results_by_gender = self.race_manager.get_results_by_gender(race_category_id, only_finished=True)

            gender_label_map = {"M": "General Masculino", "F": "General Femenino", "X": "General No Binario", "O": "General Otro"}
            present_genders = [g for g in ["M", "F", "X", "O"] if results_by_gender.get(g)]
            for gender_key in present_genders:
                gender_results = results_by_gender.get(gender_key, [])
                if not gender_results:
                    continue

                gender_name = gender_label_map.get(gender_key, f"General {gender_key}")

                # Crear grupo para general
                group = QGroupBox(f"🏆 {gender_name}")
                group.setStyleSheet("""
                    QGroupBox {
                        font-weight: bold;
                        border: 3px solid #3b82f6;
                        border-radius: 5px;
                        margin-top: 10px;
                        padding-top: 10px;
                        background-color: #eff6ff;
                    }
                    QGroupBox::title {
                        color: #1e40af;
                        subcontrol-origin: margin;
                        left: 10px;
                        padding: 0 5px;
                        font-size: 14px;
                    }
                """)

                group_layout = QVBoxLayout(group)

                # Crear tabla
                podium_table = QTableWidget()
                podium_table.setColumnCount(5)
                podium_table.setHorizontalHeaderLabels([
                    "Pos", "Dorsal", "Nombre", "Tiempo", "Edad"
                ])

                display_results = gender_results[:top_n]
                podium_table.setRowCount(len(display_results))

                for idx, result in enumerate(display_results):
                    position = idx + 1

                    # Posición con medalla
                    pos_item = QTableWidgetItem()
                    if position == 1:
                        pos_item.setText("🥇 1°")
                        pos_item.setBackground(QColor("#ffd700"))
                    elif position == 2:
                        pos_item.setText("🥈 2°")
                        pos_item.setBackground(QColor("#c0c0c0"))
                    elif position == 3:
                        pos_item.setText("🥉 3°")
                        pos_item.setBackground(QColor("#cd7f32"))
                    else:
                        pos_item.setText(f"{position}°")

                    pos_item.setFont(QFont("Arial", 12, QFont.Weight.Bold))
                    podium_table.setItem(idx, 0, pos_item)

                    # Dorsal
                    podium_table.setItem(idx, 1, QTableWidgetItem(str(result.athlete.bib_number)))

                    # Nombre
                    name_item = QTableWidgetItem(result.athlete.name)
                    name_item.setFont(QFont("Arial", 10, QFont.Weight.Bold if position <= 3 else QFont.Weight.Normal))
                    podium_table.setItem(idx, 2, name_item)

                    # Tiempo
                    time_item = QTableWidgetItem(result.get_formatted_time())
                    time_item.setFont(QFont("Arial", 10, QFont.Weight.Bold if position <= 3 else QFont.Weight.Normal))
                    podium_table.setItem(idx, 3, time_item)

                    # Edad
                    age = result.athlete.get_age()
                    age_str = f"{age} años" if age is not None else "N/D"
                    podium_table.setItem(idx, 4, QTableWidgetItem(age_str))

                # Configurar tabla
                header = podium_table.horizontalHeader()
                header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
                header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
                header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
                header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
                header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

                podium_table.setMaximumHeight(100 + (len(display_results) * 30))
                podium_table.setAlternatingRowColors(True)

                group_layout.addWidget(podium_table)
                self.podiums_layout.addWidget(group)

            # ========== 2. CATEGORÍAS DE EDAD (IAAF, etc) ==========
            podiums = self.race_manager.get_podium_by_award_category(race_category_id, top_n=top_n)
            logger.debug(f"  Podios obtenidos: {len(podiums)} categorías")

            if not podiums and not results_by_gender.get("M") and not results_by_gender.get("F"):
                no_data_label = QLabel("No hay resultados finalizados aún.")
                no_data_label.setStyleSheet("color: #f59e0b; font-style: italic; padding: 20px;")
                no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.podiums_layout.addWidget(no_data_label)
                return

            # Crear grupos de podios por categoría
            for award_cat_id, podium in podiums.items():
                award_cat = self.race_manager.get_award_category(award_cat_id)
                if not award_cat or len(podium) == 0:
                    continue

                # Crear grupo para esta categoría
                group = QGroupBox(f"🏆 {award_cat.name}")
                group.setStyleSheet("""
                    QGroupBox {
                        font-weight: bold;
                        border: 2px solid #10b981;
                        border-radius: 5px;
                        margin-top: 10px;
                        padding-top: 10px;
                    }
                    QGroupBox::title {
                        color: #10b981;
                        subcontrol-origin: margin;
                        left: 10px;
                        padding: 0 5px;
                    }
                """)

                group_layout = QVBoxLayout(group)

                # Crear tabla de podio para esta categoría
                podium_table = QTableWidget()
                podium_table.setColumnCount(5)
                podium_table.setHorizontalHeaderLabels([
                    "Pos", "Dorsal", "Nombre", "Tiempo", "Género/Edad"
                ])

                podium_table.setRowCount(len(podium))

                for idx, (position, result) in enumerate(podium):
                    # Posición con medalla
                    pos_item = QTableWidgetItem()
                    if position == 1:
                        pos_item.setText("🥇 1°")
                        pos_item.setBackground(QColor("#ffd700"))  # Oro
                    elif position == 2:
                        pos_item.setText("🥈 2°")
                        pos_item.setBackground(QColor("#c0c0c0"))  # Plata
                    elif position == 3:
                        pos_item.setText("🥉 3°")
                        pos_item.setBackground(QColor("#cd7f32"))  # Bronce
                    else:
                        pos_item.setText(f"{position}°")

                    pos_item.setFont(QFont("Arial", 12, QFont.Weight.Bold))
                    podium_table.setItem(idx, 0, pos_item)

                    # Dorsal
                    podium_table.setItem(idx, 1, QTableWidgetItem(str(result.athlete.bib_number)))

                    # Nombre
                    name_item = QTableWidgetItem(result.athlete.name)
                    name_item.setFont(QFont("Arial", 10, QFont.Weight.Bold if position <= 3 else QFont.Weight.Normal))
                    podium_table.setItem(idx, 2, name_item)

                    # Tiempo
                    time_item = QTableWidgetItem(result.get_formatted_time())
                    time_item.setFont(QFont("Arial", 10, QFont.Weight.Bold if position <= 3 else QFont.Weight.Normal))
                    podium_table.setItem(idx, 3, time_item)

                    # Género/Edad
                    gender_map = {"M": "Masculino", "F": "Femenino", "O": "Otro"}
                    gender_str = gender_map.get(result.athlete.gender, "N/D")
                    age = result.athlete.get_age()
                    age_str = f"{age} años" if age is not None else "N/D"
                    podium_table.setItem(idx, 4, QTableWidgetItem(f"{gender_str}, {age_str}"))

                # Configurar tabla
                header = podium_table.horizontalHeader()
                header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
                header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
                header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
                header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
                header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

                podium_table.setMaximumHeight(100 + (len(podium) * 30))
                podium_table.setAlternatingRowColors(True)

                group_layout.addWidget(podium_table)
                self.podiums_layout.addWidget(group)

        except Exception as e:
            error_label = QLabel(f"Error generando podios: {str(e)}")
            error_label.setStyleSheet("color: #ef4444; font-style: italic; padding: 20px;")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.podiums_layout.addWidget(error_label)
            import logging
            logging.error(f"Error en refresh_podiums: {e}", exc_info=True)

    def refresh_podiums_category_combo(self):
        """Actualizar combo de categorías para podios"""
        if not self.race_manager:
            return

        current_text = self.podiums_category_combo.currentText()
        self.podiums_category_combo.clear()
        self.podiums_category_combo.addItem("Todas las distancias")

        for category in self.race_manager.get_all_categories():
            from src.core.race_tracking.models import RaceStatus
            if category.status in [RaceStatus.RUNNING, RaceStatus.FINISHED]:
                self.podiums_category_combo.addItem(f"{category.distance_id} - {category.name}")

        # Restaurar selección si es posible
        index = self.podiums_category_combo.findText(current_text)
        if index >= 0:
            self.podiums_category_combo.setCurrentIndex(index)

    def refresh_splits_category_combo(self):
        """Actualizar combo de categorías para splits"""
        if not self.race_manager:
            return

        current_text = self.splits_category_combo.currentText()
        self.splits_category_combo.clear()
        self.splits_category_combo.addItem("Selecciona una distancia")

        count_added = 0
        for category in self.race_manager.get_all_categories():
            # Mostrar todas las categorías RUNNING o FINISHED
            from src.core.race_tracking.models import RaceStatus
            if category.status in [RaceStatus.RUNNING, RaceStatus.FINISHED]:
                # Agregar indicador si tiene checkpoints o no
                if category.expected_checkpoints > 0:
                    self.splits_category_combo.addItem(
                        f"{category.distance_id} - {category.name} ({category.expected_checkpoints} CPs)"
                    )
                else:
                    self.splits_category_combo.addItem(
                        f"{category.distance_id} - {category.name} (sin CPs)"
                    )
                count_added += 1

        # Restaurar selección si es posible
        index = self.splits_category_combo.findText(current_text)
        if index >= 0:
            self.splits_category_combo.setCurrentIndex(index)

    def export_podiums_to_csv(self):
        """Exportar podios por categoría de premiación a CSV"""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        import csv

        if not self.race_manager:
            QMessageBox.warning(self, "Error", "No hay race_manager disponible")
            return

        selected_text = self.podiums_category_combo.currentText()

        # Si está en "Todas las distancias", delegar al exportador completo
        if selected_text == "Todas las distancias":
            self.export_all_podiums_to_csv()
            return

        race_category_id = selected_text.split(" - ")[0]
        race_category = self.race_manager.get_category(race_category_id)

        # Diálogo para seleccionar archivo
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Podios a CSV",
            f"podios_{race_category_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )

        if not file_path:
            return  # Usuario canceló

        try:
            # Obtener podios
            top_n = int(self.podium_top_n_combo.currentText())
            podiums = self.race_manager.get_podium_by_award_category(race_category_id, top_n=top_n)

            if not podiums:
                QMessageBox.warning(self, "Sin datos", "No hay resultados finalizados para exportar")
                return

            # Escribir CSV
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)

                # Encabezado principal
                writer.writerow([f"PODIOS POR CATEGORÍA DE PREMIACIÓN - {race_category.name}"])
                writer.writerow([f"Fecha de exportación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
                writer.writerow([])  # Línea vacía

                # Para cada categoría de premiación
                for award_cat_id, podium in sorted(podiums.items()):
                    award_cat = self.race_manager.get_award_category(award_cat_id)
                    if not award_cat or len(podium) == 0:
                        continue

                    # Encabezado de categoría
                    writer.writerow([f"CATEGORÍA: {award_cat.name}"])
                    writer.writerow([
                        "Posición",
                        "Dorsal",
                        "Nombre",
                        "Tiempo",
                        "Género",
                        "Edad",
                        "Equipo"
                    ])

                    # Resultados de esta categoría
                    for position, result in podium:
                        gender_map = {"M": "Masculino", "F": "Femenino", "O": "Otro"}
                        gender_str = gender_map.get(result.athlete.gender, "N/D")
                        age = result.athlete.get_age()
                        age_str = str(age) if age is not None else "N/D"

                        writer.writerow([
                            position,
                            result.athlete.bib_number,
                            result.athlete.name,
                            result.get_formatted_time(),
                            gender_str,
                            age_str,
                            result.athlete.team or ""
                        ])

                    writer.writerow([])  # Línea vacía entre categorías

                # Clasificación General por Género
                writer.writerow([])
                writer.writerow(["=" * 80])
                writer.writerow(["CLASIFICACIÓN GENERAL POR GÉNERO"])
                writer.writerow(["=" * 80])
                writer.writerow([])

                results_by_gender = self.race_manager.get_results_by_gender(race_category_id, only_finished=True)

                for gender_key, gender_name in [("M", "GENERAL MASCULINO"), ("F", "GENERAL FEMENINO")]:
                    gender_results = results_by_gender.get(gender_key, [])
                    if not gender_results:
                        continue

                    writer.writerow([gender_name])
                    writer.writerow([
                        "Pos",
                        "Dorsal",
                        "Nombre",
                        "Tiempo",
                        "Categoría",
                        "Edad",
                        "Equipo"
                    ])

                    for position, result in enumerate(gender_results[:top_n], 1):
                        age = result.athlete.get_age()
                        age_str = str(age) if age is not None else "N/D"

                        writer.writerow([
                            position,
                            result.athlete.bib_number,
                            result.athlete.name,
                            result.get_formatted_time(),
                            result.athlete.get_category() or "N/D",
                            age_str,
                            result.athlete.team or ""
                        ])

                    writer.writerow([])  # Línea vacía

                # Estadísticas generales al final
                writer.writerow([])
                writer.writerow(["ESTADÍSTICAS GENERALES"])
                writer.writerow(["Total de categorías de premiación:", len(podiums)])
                total_podium_positions = sum(len(p) for p in podiums.values())
                writer.writerow(["Total de posiciones en podios:", total_podium_positions])
                writer.writerow(["Finalizadores masculinos:", len(results_by_gender.get('M', []))])
                writer.writerow(["Finalizadores femeninos:", len(results_by_gender.get('F', []))])

            QMessageBox.information(
                self,
                "Éxito",
                f"Podios exportados exitosamente a:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error exportando podios:\n{str(e)}"
            )
            import logging
            logging.error(f"Error en export_podiums_to_csv: {e}", exc_info=True)

    def export_all_podiums_to_csv(self):
        """Exportar podios de todas las distancias en un único CSV"""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        import csv

        if not self.race_manager:
            QMessageBox.warning(self, "Error", "No hay race_manager disponible")
            return

        distances = self.race_manager.get_all_categories()
        if not distances:
            QMessageBox.warning(self, "Sin datos", "No hay distancias configuradas")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Podios de Todas las Distancias",
            f"podios_todas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )
        if not file_path:
            return

        top_n = int(self.podium_top_n_combo.currentText())

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([f"PODIOS - TODAS LAS DISTANCIAS"])
                writer.writerow([f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
                writer.writerow([f"Top N: {top_n}"])
                writer.writerow([])

                exported_any = False

                for distance in distances:
                    dist_id = distance.distance_id
                    podiums = self.race_manager.get_podium_by_award_category(dist_id, top_n=top_n)
                    results_by_gender = self.race_manager.get_results_by_gender(dist_id, only_finished=True)

                    total_finished = sum(
                        len(v) for v in results_by_gender.values()
                    )
                    if total_finished == 0 and not any(
                        len(p) > 0 for p in (podiums or {}).values()
                    ):
                        continue  # Distancia sin finalizados, saltar

                    exported_any = True
                    separator = "=" * 60
                    writer.writerow([separator])
                    writer.writerow([f"DISTANCIA: {distance.name}  ({dist_id})"])
                    writer.writerow([separator])
                    writer.writerow([])

                    # Podios por categoría de premiación
                    if podiums:
                        writer.writerow(["PODIOS POR CATEGORÍA DE PREMIACIÓN"])
                        writer.writerow(["Posición", "Dorsal", "Nombre", "Tiempo", "Género", "Edad", "Equipo", "Categoría Premiación"])
                        for award_cat_id, podium in sorted(podiums.items()):
                            award_cat = self.race_manager.get_award_category(award_cat_id)
                            if not award_cat or not podium:
                                continue
                            for position, result in podium:
                                gender_map = {"M": "Masculino", "F": "Femenino", "O": "Otro"}
                                age = result.athlete.get_age()
                                writer.writerow([
                                    position,
                                    result.athlete.bib_number,
                                    result.athlete.name,
                                    result.get_formatted_time(),
                                    gender_map.get(result.athlete.gender, "N/D"),
                                    age if age is not None else "N/D",
                                    result.athlete.team or "",
                                    award_cat.name,
                                ])
                        writer.writerow([])

                    # General por género
                    writer.writerow(["CLASIFICACIÓN GENERAL POR GÉNERO"])
                    writer.writerow(["Pos", "Dorsal", "Nombre", "Tiempo", "Género", "Edad", "Equipo"])
                    for gender_key, gender_label in [("M", "Masculino"), ("F", "Femenino"), ("O", "No Binario")]:
                        gender_results = results_by_gender.get(gender_key, [])
                        for pos, result in enumerate(gender_results[:top_n], 1):
                            age = result.athlete.get_age()
                            writer.writerow([
                                pos,
                                result.athlete.bib_number,
                                result.athlete.name,
                                result.get_formatted_time(),
                                gender_label,
                                age if age is not None else "N/D",
                                result.athlete.team or "",
                            ])
                    writer.writerow([])

                if not exported_any:
                    QMessageBox.warning(self, "Sin datos", "Ninguna distancia tiene finalizados aún")
                    return

            QMessageBox.information(self, "Éxito", f"Podios exportados a:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error exportando:\n{str(e)}")
            logger.error(f"Error en export_all_podiums_to_csv: {e}", exc_info=True)

    def _get_event_name(self):
        """Obtiene el nombre del evento desde el agente configurado (.szconfig)"""
        try:
            main_window = self.window()
            if hasattr(main_window, 'tab_manager'):
                config_tab = main_window.tab_manager.get_tab('configuration')
                if config_tab and hasattr(config_tab, 'cloud_agent_input'):
                    name = config_tab.cloud_agent_input.text().strip()
                    if name:
                        return name
        except Exception:
            pass
        return "Carrera"

    def _build_distance_data(self, distance_id: str, top_n: int) -> dict:
        """Recopila todos los datos necesarios para exportar una distancia"""
        distance = self.race_manager.get_distance(distance_id)
        all_results = self.race_manager.get_results(distance_id)
        results_by_gender = self.race_manager.get_results_by_gender(distance_id, only_finished=True)
        podiums = self.race_manager.get_podium_by_award_category(distance_id, top_n=top_n) or {}
        results_by_category = self.race_manager.get_results_by_award_category(distance_id)
        # Incluir TODAS las award categories disponibles para la distancia,
        # no solo las que tienen podio (podría estar vacío si faltan birth_date)
        all_award_cats = self.race_manager.get_award_categories_for_distance(distance_id)
        award_categories = {ac.award_category_id: ac for ac in all_award_cats}
        # Agregar también las que vienen de podiums y results_by_category
        for aid in list(podiums) + list(results_by_category):
            if aid not in award_categories:
                ac = self.race_manager.get_award_category(aid)
                if ac:
                    award_categories[aid] = ac
        return {
            'distance': distance,
            'all_results': all_results,
            'results_by_gender': results_by_gender,
            'podiums_by_award_cat': podiums,
            'award_categories': award_categories,
            'results_by_category': results_by_category,
        }

    def _export_pdf_all_distances(self, kind: str):
        """Exporta todas las distancias en un único PDF"""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from src.utils.pdf_exporter import PDFExporter

        distances = self.race_manager.get_all_categories()
        if not distances:
            QMessageBox.warning(self, "Sin datos", "No hay distancias configuradas")
            return

        kind_labels = {
            'full':       ('PDF General — Todas las distancias', 'podios_general_todas'),
            'gender':     ('PDF Género — Todas las distancias',  'genero_todas'),
            'categories': ('PDF Categorías — Todas las distancias', 'categorias_todas'),
            'announcer':  ('PDF Relator — Todas las distancias', 'relator_todas'),
        }
        dialog_title, default_name = kind_labels.get(kind, ('PDF Todas', 'todas'))

        file_path, _ = QFileDialog.getSaveFileName(
            self, dialog_title,
            f"{default_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "PDF Files (*.pdf)"
        )
        if not file_path:
            return

        top_n = int(self.podium_top_n_combo.currentText())
        distances_data = []
        for d in distances:
            data = self._build_distance_data(d.distance_id, top_n)
            # Incluir cualquier distancia que tenga al menos un resultado
            if data['all_results']:
                distances_data.append(data)

        if not distances_data:
            QMessageBox.warning(self, "Sin datos", "Ninguna distancia está en curso o finalizada")
            return

        try:
            exporter = PDFExporter(event_name=self._get_event_name())
            exporter.export_multi_distance(distances_data, kind=kind, output_path=file_path)
            QMessageBox.information(self, "Éxito", f"PDF exportado:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error exportando PDF:\n{str(e)}")
            logger.error(f"Error en _export_pdf_all_distances({kind}): {e}", exc_info=True)

    def export_pdf_complete(self):
        """Exportar PDF completo: orden de llegada + clasificaciones por género + categorías"""
        self.export_pdf_general()

    def export_pdf_general(self):
        """Exportar PDF completo con toda la clasificación"""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from src.utils.pdf_exporter import PDFExporter
        import logging
        logger = logging.getLogger(__name__)

        logger.info("📕 Exportación a PDF General iniciada")

        if not self.race_manager:
            QMessageBox.warning(self, "Sin Race Manager", "No hay race manager configurado")
            return

        # Obtener distancia seleccionada del combo de podios
        selected_text = self.podiums_category_combo.currentText()
        logger.info(f"  Distancia seleccionada: {selected_text}")

        if selected_text == "Todas las distancias":
            self._export_pdf_all_distances('full')
            return

        # Extraer distance_id del formato "distance_id - nombre"
        race_category_id = selected_text.split(" - ")[0]
        logger.info(f"  Distance ID extraído: {race_category_id}")

        distance = self.race_manager.get_distance(race_category_id)
        if not distance:
            logger.error(f"  ❌ Distancia {race_category_id} no encontrada")
            return

        logger.info(f"  Distancia: {distance.name} ({len(distance.participants)} participantes)")

        try:
            # Diálogo para seleccionar archivo
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Exportar Clasificación General a PDF",
                f"clasificacion_general_{race_category_id}.pdf",
                "PDF Files (*.pdf)"
            )

            if not file_path:
                logger.info("  Usuario canceló selección de archivo")
                return

            logger.info(f"  Archivo de salida: {file_path}")

            # Obtener resultados
            results = self.race_manager.get_results(race_category_id)
            logger.info(f"  Resultados obtenidos: {len(results)}")

            if not results:
                QMessageBox.warning(self, "Sin resultados", "No hay resultados para exportar")
                return

            # Crear exporter
            logger.info("  Creando PDFExporter...")
            exporter = PDFExporter(event_name=self._get_event_name())

            # Obtener datos completos para el PDF estilo frontend
            results_by_gender = self.race_manager.get_results_by_gender(race_category_id, only_finished=True)
            top_n = int(self.podium_top_n_combo.currentText())
            podiums = self.race_manager.get_podium_by_award_category(race_category_id, top_n=top_n) or {}
            results_by_award_cat = self.race_manager.get_results_by_award_category(race_category_id) or {}
            award_categories = {}
            for award_id in list(podiums) + list(results_by_award_cat):
                ac = self.race_manager.get_award_category(award_id)
                if ac:
                    award_categories[award_id] = ac

            logger.info("  Generando PDF completo (estilo frontend)...")
            exporter.export_full_results(
                distance_name=distance.name,
                distance_meters=getattr(distance, 'distance_meters', 0),
                all_results=results,
                results_by_gender=results_by_gender,
                podiums_by_award_cat=podiums,
                award_categories=award_categories,
                output_path=file_path,
                results_by_award_cat=results_by_award_cat,
            )

            logger.info(f"✅ PDF generado exitosamente: {file_path}")

            QMessageBox.information(
                self,
                "Éxito",
                f"PDF de clasificación general exportado:\n{file_path}"
            )

        except Exception as e:
            logger.error(f"❌ Error en export_pdf_general: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error exportando PDF:\n{str(e)}\n\nRevisa la consola para más detalles")

    def export_pdf_by_gender(self):
        """Exportar clasificación por género a PDF"""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from src.utils.pdf_exporter import PDFExporter
        import logging
        logger = logging.getLogger(__name__)

        logger.info("📗 Exportación a PDF por Género iniciada")

        if not self.race_manager:
            QMessageBox.warning(self, "Sin Race Manager", "No hay race manager configurado")
            return

        # Obtener distancia del combo de podios
        selected_text = self.podiums_category_combo.currentText()
        if selected_text == "Todas las distancias":
            self._export_pdf_all_distances('gender')
            return

        race_category_id = selected_text.split(" - ")[0]
        logger.info(f"  Distance ID: {race_category_id}")

        distance = self.race_manager.get_distance(race_category_id)
        if not distance:
            logger.error(f"  ❌ Distancia {race_category_id} no encontrada")
            return

        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Exportar Clasificación por Género a PDF",
                f"clasificacion_genero_{race_category_id}.pdf",
                "PDF Files (*.pdf)"
            )

            if not file_path:
                logger.info("  Usuario canceló selección de archivo")
                return

            # Obtener clasificación por género
            results_by_gender = self.race_manager.get_results_by_gender(race_category_id)
            logger.info(f"  Masculino: {len(results_by_gender.get('M', []))}")
            logger.info(f"  Femenino: {len(results_by_gender.get('F', []))}")

            exporter = PDFExporter(event_name=self._get_event_name())
            exporter.export_classification_by_gender(
                distance_name=distance.name,
                results_by_gender=results_by_gender,
                output_path=file_path,
                distance_meters=getattr(distance, 'distance_meters', 0),
            )

            logger.info(f"✅ PDF por género generado: {file_path}")

            QMessageBox.information(
                self,
                "Éxito",
                f"PDF por género exportado:\n{file_path}"
            )

        except Exception as e:
            logger.error(f"❌ Error en export_pdf_by_gender: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error exportando PDF:\n{str(e)}\n\nRevisa la consola para más detalles")

    def export_pdf_by_category(self):
        """Exportar clasificación por categorías IAAF a PDF"""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from src.utils.pdf_exporter import PDFExporter

        if not self.race_manager:
            QMessageBox.warning(self, "Sin Race Manager", "No hay race manager configurado")
            return

        # Obtener distancia del combo de podios
        selected_text = self.podiums_category_combo.currentText()
        if selected_text == "Todas las distancias":
            self._export_pdf_all_distances('categories')
            return

        race_category_id = selected_text.split(" - ")[0]
        logger.info(f"  Distance ID: {race_category_id}")

        distance = self.race_manager.get_distance(race_category_id)
        if not distance:
            logger.error(f"  ❌ Distancia {race_category_id} no encontrada")
            return

        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Exportar Clasificación por Categorías a PDF",
                f"clasificacion_categorias_{race_category_id}.pdf",
                "PDF Files (*.pdf)"
            )

            if not file_path:
                return

            # Obtener clasificación por categorías
            results_by_category = self.race_manager.get_results_by_award_category(race_category_id)

            exporter = PDFExporter(event_name=self._get_event_name())
            exporter.export_classification_by_category(
                distance_name=distance.name,
                results_by_category=results_by_category,
                output_path=file_path,
                distance_meters=getattr(distance, 'distance_meters', 0),
            )

            QMessageBox.information(
                self,
                "Éxito",
                f"PDF por categorías exportado:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error exportando PDF:\n{str(e)}")
            import logging
            logging.error(f"Error en export_pdf_by_category: {e}", exc_info=True)

    def export_pdf_announcer(self):
        """Exportar formato para relator a PDF"""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from src.utils.pdf_exporter import PDFExporter

        if not self.race_manager:
            QMessageBox.warning(self, "Sin Race Manager", "No hay race manager configurado")
            return

        # Obtener distancia del combo de podios
        selected_text = self.podiums_category_combo.currentText()
        if selected_text == "Todas las distancias":
            self._export_pdf_all_distances('announcer')
            return

        race_category_id = selected_text.split(" - ")[0]
        logger.info(f"  Distance ID: {race_category_id}")

        distance = self.race_manager.get_distance(race_category_id)
        if not distance:
            logger.error(f"  ❌ Distancia {race_category_id} no encontrada")
            return

        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Exportar Formato para Relator a PDF",
                f"relator_{race_category_id}.pdf",
                "PDF Files (*.pdf)"
            )

            if not file_path:
                return

            # Obtener resultados
            results = self.race_manager.get_results(race_category_id)

            exporter = PDFExporter(event_name=self._get_event_name())
            exporter.export_announcer_format(
                distance_name=distance.name,
                results=results,
                output_path=file_path,
                distance_meters=getattr(distance, 'distance_meters', 0),
            )

            QMessageBox.information(
                self,
                "Éxito",
                f"PDF para relator exportado:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error exportando PDF:\n{str(e)}")
            import logging
            logging.error(f"Error en export_pdf_announcer: {e}", exc_info=True)

    def set_race_manager(self, race_manager):
        """Establecer el race manager"""
        self.race_manager = race_manager
        if race_manager:
            self.refresh_category_combo()
            self.system_status_label.setText("Sistema: Conectado")
            self.system_status_label.setStyleSheet("font-weight: bold; color: green;")
        
    def refresh_category_combo(self):
        """Actualizar combo de categorías"""
        if not self.race_manager:
            return

        current_text = self.category_combo.currentText()
        self.category_combo.clear()
        self.category_combo.addItem("Todas las categorías")

        for category in self.race_manager.get_all_categories():
            self.category_combo.addItem(f"{category.distance_id} - {category.name}")

        # Restaurar selección si es posible
        index = self.category_combo.findText(current_text)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)

        # También actualizar el combo de podios y splits
        self.refresh_podiums_category_combo()
        self.refresh_splits_category_combo()
        
    def on_category_changed(self):
        """Manejar cambio de categoría seleccionada"""
        self.refresh_participants_table()
        self._update_bulk_start_btn_state()

    def _update_bulk_start_btn_state(self):
        """Habilitar el botón de largada masiva solo cuando hay gun_time en la distancia seleccionada."""
        if not self.race_manager:
            self.bulk_start_btn.setEnabled(False)
            self.bulk_start_btn.setToolTip("Sin race manager configurado.")
            return

        selected_text = self.category_combo.currentText()
        if selected_text == "Todas las categorías":
            self.bulk_start_btn.setEnabled(False)
            self.bulk_start_btn.setToolTip("Seleccioná una distancia específica para usar esta función.")
            return

        distance_id = selected_text.split(" - ")[0]
        category = self.race_manager.get_category(distance_id)
        has_gun = category is not None and category.start_time is not None

        self.bulk_start_btn.setEnabled(has_gun)
        if has_gun:
            gun_str = category.start_time.strftime('%H:%M:%S')
            self.bulk_start_btn.setToolTip(
                f"Asigna el tiempo de disparo ({gun_str}) a todos los atletas\n"
                "de esta distancia que no tienen largada registrada."
            )
        else:
            self.bulk_start_btn.setToolTip(
                "La distancia no tiene tiempo de disparo registrado.\n"
                "Iniciá la carrera primero."
            )
        
    def toggle_auto_refresh(self):
        """Alternar actualización automática"""
        if self.refresh_timer.isActive():
            self.refresh_timer.stop()
            self.auto_refresh_btn.setText("Auto: OFF")
            self.auto_refresh_btn.setStyleSheet("background-color: red; color: white;")
        else:
            self.refresh_timer.start(2000)
            self.auto_refresh_btn.setText("Auto: ON")
            self.auto_refresh_btn.setStyleSheet("background-color: green; color: white;")
            
    def refresh(self):
        """Actualizar widget completo (para compatibilidad con señales)"""
        self.refresh_category_combo()
        self.refresh_all_data()

    def refresh_all_data(self):
        """Actualizar todos los datos"""
        if not self.race_manager:
            return

        self.refresh_categories_overview()
        self.refresh_participants_table()
        self.refresh_statistics()
        self._update_bulk_start_btn_state()
        
    def refresh_categories_overview(self):
        """Actualizar resumen de categorías"""
        if not self.race_manager:
            return

        self.categories_overview_table.setRowCount(0)

        for category in self.race_manager.get_all_categories():
            # Obtener resultados de esta categoría
            results = self.race_manager.get_results(category.distance_id)

            # Contar por estado
            from src.core.race_tracking.models import AthleteStatus
            not_started = len([r for r in results if r.status == AthleteStatus.NOT_STARTED])
            in_progress = len([r for r in results if r.status == AthleteStatus.RUNNING])
            finished = len([r for r in results if r.status == AthleteStatus.FINISHED])
            total_participants = len(results)

            # Última actividad
            last_checkpoint = "N/A"
            if results:
                # Encontrar el último timestamp de cualquier resultado
                timestamps = []
                for r in results:
                    if r.start_time:
                        timestamps.append(r.start_time)
                    if r.finish_time:
                        timestamps.append(r.finish_time)
                    for cp_time in r.checkpoint_times.values():
                        timestamps.append(cp_time)

                if timestamps:
                    last_checkpoint = max(timestamps).strftime('%H:%M:%S')

            # Agregar fila
            row = self.categories_overview_table.rowCount()
            self.categories_overview_table.insertRow(row)

            self.categories_overview_table.setItem(row, 0,
                                                  QTableWidgetItem(f"{category.distance_id} - {category.name}"))

            # Estado con color
            from src.core.race_tracking.models import RaceStatus
            status_item = QTableWidgetItem(category.status.value.title())
            if category.status == RaceStatus.RUNNING:
                status_item.setBackground(Qt.GlobalColor.green)
            elif category.status == RaceStatus.FINISHED:
                status_item.setBackground(Qt.GlobalColor.gray)
            self.categories_overview_table.setItem(row, 1, status_item)

            # Hora de inicio
            start_time_str = category.start_time.strftime('%H:%M:%S') if category.start_time else "No iniciada"
            self.categories_overview_table.setItem(row, 2, QTableWidgetItem(start_time_str))

            self.categories_overview_table.setItem(row, 3, QTableWidgetItem(str(total_participants)))
            self.categories_overview_table.setItem(row, 4, QTableWidgetItem(str(not_started)))
            self.categories_overview_table.setItem(row, 5, QTableWidgetItem(str(in_progress)))
            self.categories_overview_table.setItem(row, 6, QTableWidgetItem(str(finished)))
            self.categories_overview_table.setItem(row, 7, QTableWidgetItem(last_checkpoint))
            
    def refresh_participants_table(self):
        """Actualizar tabla de participantes"""
        if not self.race_manager:
            return
            
        self.participants_table.setRowCount(0)
        
        # Determinar categoría seleccionada
        selected_category = None
        current_text = self.category_combo.currentText()
        if current_text != "Todas las categorías" and " - " in current_text:
            selected_category = current_text.split(" - ")[0]
            
        # Filtrar por estado
        status_filter = self.status_filter_combo.currentText().lower()
        
        # Obtener participantes
        all_participants = []
        if selected_category:
            all_participants = self.race_manager.get_results(selected_category)
        else:
            # Todas las categorías
            for category in self.race_manager.get_all_categories():
                all_participants.extend(self.race_manager.get_results(category.distance_id))
        
        # Filtrar por estado
        if status_filter != "todos":
            from src.core.race_tracking.models import AthleteStatus
            status_map = {
                "no iniciados": AthleteStatus.NOT_STARTED,
                "en carrera": AthleteStatus.RUNNING,
                "finalizados": AthleteStatus.FINISHED
            }
            filter_status = status_map.get(status_filter)
            if filter_status:
                all_participants = [p for p in all_participants if p.status == filter_status]
        
        # Actualizar contador
        self.participants_count_label.setText(f"Total: {len(all_participants)} participantes")
        
        # Llenar tabla
        from src.core.race_tracking.models import AthleteStatus
        for result in all_participants:
            row = self.participants_table.rowCount()
            self.participants_table.insertRow(row)

            # Chip ID, Categoría
            self.participants_table.setItem(row, 0, QTableWidgetItem(result.athlete.tag_id))
            self.participants_table.setItem(row, 1, QTableWidgetItem(result.distance_id))

            # Estado con color
            status_item = QTableWidgetItem(result.status.value.replace('_', ' ').title())
            if result.status == AthleteStatus.RUNNING:
                status_item.setBackground(Qt.GlobalColor.yellow)
            elif result.status == AthleteStatus.FINISHED:
                status_item.setBackground(Qt.GlobalColor.green)
            self.participants_table.setItem(row, 2, status_item)

            # Tiempos
            start_time_str = result.start_time.strftime('%H:%M:%S') if result.start_time else "N/A"
            self.participants_table.setItem(row, 3, QTableWidgetItem(start_time_str))

            # Tiempo actual/total
            if result.status == AthleteStatus.FINISHED and result.total_time:
                time_str = result.get_formatted_time()
            elif result.status == AthleteStatus.RUNNING and result.start_time:
                current_time = (datetime.now() - result.start_time).total_seconds()
                minutes = int(current_time // 60)
                seconds = int(current_time % 60)
                time_str = f"{minutes:02d}:{seconds:02d} (en curso)"
            else:
                time_str = "N/A"
            self.participants_table.setItem(row, 4, QTableWidgetItem(time_str))

            # Checkpoints - Mostrar cuáles checkpoints específicos pasó
            if result.checkpoint_times:
                # Obtener lista de checkpoints en orden
                checkpoint_numbers = sorted(result.checkpoint_times.keys())
                checkpoints_text = ", ".join([f"✓ CP{num}" for num in checkpoint_numbers])
                checkpoints_item = QTableWidgetItem(checkpoints_text)
                checkpoints_item.setForeground(QColor(0, 100, 200))  # Azul
            else:
                checkpoints_item = QTableWidgetItem("-")
            self.participants_table.setItem(row, 5, checkpoints_item)

            # Última lectura (último timestamp conocido)
            last_time = None
            last_antenna = "N/A"
            if result.finish_time:
                last_time = result.finish_time
                last_antenna = "Finish"
            elif result.checkpoint_times:
                last_checkpoint = max(result.checkpoint_times.keys())
                last_time = result.checkpoint_times[last_checkpoint]
                last_antenna = f"CP{last_checkpoint}"
            elif result.start_time:
                last_time = result.start_time
                last_antenna = "Start"

            last_reading_str = last_time.strftime('%H:%M:%S') if last_time else "N/A"

            self.participants_table.setItem(row, 6, QTableWidgetItem(last_reading_str))
            self.participants_table.setItem(row, 7, QTableWidgetItem(last_antenna))
            
    def refresh_statistics(self):
        """Actualizar estadísticas"""
        if not self.race_manager:
            return

        # Calcular estadísticas
        active_categories = self.race_manager.get_active_categories()
        all_categories = self.race_manager.get_all_categories()

        total_participants = 0
        total_in_race = 0
        total_finished = 0
        total_detections = len(self.race_manager.detection_history)

        from src.core.race_tracking.models import AthleteStatus

        stats_text = f"""ESTADÍSTICAS DEL SISTEMA
{'='*30}
Distancias activas: {len(active_categories)}
Total de distancias: {len(all_categories)}
Total de detecciones: {total_detections}

PARTICIPANTES POR DISTANCIA:
"""

        for category in all_categories:
            results = self.race_manager.get_results(category.distance_id)
            num_participants = len(results)
            num_running = len([r for r in results if r.status == AthleteStatus.RUNNING])
            num_finished = len([r for r in results if r.status == AthleteStatus.FINISHED])

            total_participants += num_participants
            total_in_race += num_running
            total_finished += num_finished

            stats_text += f"• {category.name}:\n"
            stats_text += f"  - Inscritos: {num_participants}\n"
            stats_text += f"  - En carrera: {num_running}\n"
            stats_text += f"  - Finalizados: {num_finished}\n\n"

        stats_text += f"""TOTALES:
- Total inscritos: {total_participants}
- Total en carrera: {total_in_race}
- Total finalizados: {total_finished}

Última actualización: {datetime.now().strftime('%H:%M:%S')}"""

        self.statistics_text.setPlainText(stats_text)
        
    def log_event(self, message):
        """Agregar evento al log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        self.events_log.append(log_message)
        
        # Mantener máximo 50 líneas en el log
        text = self.events_log.toPlainText()
        lines = text.split('\n')
        if len(lines) > 50:
            self.events_log.setPlainText('\n'.join(lines[-50:]))

    def show_export_dialog(self):
        """Mostrar diálogo de exportación de resultados"""
        try:
            from .export_results_dialog import ExportResultsDialog

            dialog = ExportResultsDialog(self.race_manager, parent=self)
            dialog.exec()

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Error abriendo diálogo de exportación: {e}")
            import traceback
            traceback.print_exc()

            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo abrir el diálogo de exportación:\n{str(e)}"
            )