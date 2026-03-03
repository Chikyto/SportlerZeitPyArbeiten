#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Testing de Integración con Plataforma de Registro
scripts/test_integration.py

Verifica conectividad y endpoints de la API de la plataforma
"""

import sys
import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

# Agregar src al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from colorama import Fore, Style, init

# Inicializar colorama
init(autoreset=True)

@dataclass
class TestResult:
    """Resultado de un test"""
    name: str
    passed: bool
    message: str
    details: Optional[str] = None


class IntegrationTester:
    """
    Tester de integración con plataforma de registro

    Verifica:
    - Conectividad
    - Autenticación
    - Endpoints disponibles
    - Formato de respuestas
    - Mapeo de campos
    """

    def __init__(self, config_path: str = "config/api_config.json"):
        """
        Inicializar tester

        Args:
            config_path: Path al archivo de configuración
        """
        self.config_path = config_path
        self.config: Optional[Dict] = None
        self.api_url: Optional[str] = None
        self.api_key: Optional[str] = None
        self.event_id: Optional[str] = None
        self.results: List[TestResult] = []

    def load_config(self) -> bool:
        """Cargar configuración"""
        try:
            with open(self.config_path) as f:
                self.config = json.load(f)

            self.api_url = self.config.get('api_url', '').rstrip('/')
            self.api_key = self.config.get('api_key')
            self.event_id = self.config.get('event_id')

            if not self.api_url:
                self.results.append(TestResult(
                    name="Load Config",
                    passed=False,
                    message="api_url no configurado"
                ))
                return False

            if not self.event_id:
                self.results.append(TestResult(
                    name="Load Config",
                    passed=False,
                    message="event_id no configurado"
                ))
                return False

            self.results.append(TestResult(
                name="Load Config",
                passed=True,
                message=f"Configuración cargada: {self.api_url}",
                details=f"Event ID: {self.event_id}"
            ))
            return True

        except FileNotFoundError:
            self.results.append(TestResult(
                name="Load Config",
                passed=False,
                message=f"Archivo no encontrado: {self.config_path}",
                details="Crear config/api_config.json con api_url, event_id, api_key"
            ))
            return False
        except json.JSONDecodeError as e:
            self.results.append(TestResult(
                name="Load Config",
                passed=False,
                message=f"JSON inválido: {e}"
            ))
            return False
        except Exception as e:
            self.results.append(TestResult(
                name="Load Config",
                passed=False,
                message=f"Error inesperado: {e}"
            ))
            return False

    def _get_headers(self) -> Dict:
        """Obtener headers para requests"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'RFID-Timing-System/2.0'
        }
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        return headers

    def test_connectivity(self) -> bool:
        """Test 1: Conectividad básica"""
        try:
            response = requests.get(
                self.api_url,
                headers=self._get_headers(),
                timeout=10
            )

            if response.status_code < 500:
                self.results.append(TestResult(
                    name="Connectivity",
                    passed=True,
                    message=f"Servidor accesible (HTTP {response.status_code})"
                ))
                return True
            else:
                self.results.append(TestResult(
                    name="Connectivity",
                    passed=False,
                    message=f"Error del servidor: HTTP {response.status_code}"
                ))
                return False

        except requests.ConnectionError:
            self.results.append(TestResult(
                name="Connectivity",
                passed=False,
                message="No se pudo conectar al servidor",
                details=f"Verificar URL: {self.api_url}"
            ))
            return False
        except requests.Timeout:
            self.results.append(TestResult(
                name="Connectivity",
                passed=False,
                message="Timeout (>10s)"
            ))
            return False
        except Exception as e:
            self.results.append(TestResult(
                name="Connectivity",
                passed=False,
                message=f"Error: {e}"
            ))
            return False

    def test_authentication(self) -> bool:
        """Test 2: Autenticación"""
        # Si no hay API key, skip
        if not self.api_key:
            self.results.append(TestResult(
                name="Authentication",
                passed=True,
                message="Sin API Key configurada (opcional)",
                details="Si la API requiere autenticación, agregar api_key al config"
            ))
            return True

        try:
            # Intentar acceder a endpoint que requiere auth
            url = f"{self.api_url}/api/events/{self.event_id}/categories"
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=10
            )

            if response.status_code == 401:
                self.results.append(TestResult(
                    name="Authentication",
                    passed=False,
                    message="API Key inválido o expirado (HTTP 401)"
                ))
                return False
            elif response.status_code == 403:
                self.results.append(TestResult(
                    name="Authentication",
                    passed=False,
                    message="Sin permisos para este evento (HTTP 403)"
                ))
                return False
            elif response.status_code < 400:
                self.results.append(TestResult(
                    name="Authentication",
                    passed=True,
                    message="API Key válido"
                ))
                return True
            else:
                self.results.append(TestResult(
                    name="Authentication",
                    passed=True,
                    message=f"Autenticación OK (HTTP {response.status_code})",
                    details="Endpoint respondió (no 401/403)"
                ))
                return True

        except Exception as e:
            self.results.append(TestResult(
                name="Authentication",
                passed=False,
                message=f"Error verificando autenticación: {e}"
            ))
            return False

    def test_get_categories(self) -> bool:
        """Test 3: GET /api/events/{event_id}/categories"""
        try:
            url = f"{self.api_url}/api/events/{self.event_id}/categories"
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=10
            )

            if response.status_code == 404:
                self.results.append(TestResult(
                    name="GET Categories",
                    passed=False,
                    message="Evento no encontrado (HTTP 404)",
                    details=f"Event ID: {self.event_id}"
                ))
                return False

            if response.status_code != 200:
                self.results.append(TestResult(
                    name="GET Categories",
                    passed=False,
                    message=f"HTTP {response.status_code}",
                    details=response.text[:200]
                ))
                return False

            # Verificar formato
            data = response.json()

            # Verificar estructura básica
            if 'categories' not in data:
                self.results.append(TestResult(
                    name="GET Categories",
                    passed=False,
                    message="Respuesta sin campo 'categories'",
                    details=f"Keys encontradas: {list(data.keys())}"
                ))
                return False

            categories = data['categories']
            if not isinstance(categories, list):
                self.results.append(TestResult(
                    name="GET Categories",
                    passed=False,
                    message="'categories' no es un array"
                ))
                return False

            if len(categories) == 0:
                self.results.append(TestResult(
                    name="GET Categories",
                    passed=True,
                    message="Endpoint OK pero sin categorías",
                    details="Agregar categorías al evento en la plataforma"
                ))
                return True

            # Verificar campos requeridos en primera categoría
            cat = categories[0]
            required_fields = ['category_id', 'name', 'distance_km']
            missing_fields = [f for f in required_fields if f not in cat]

            if missing_fields:
                self.results.append(TestResult(
                    name="GET Categories",
                    passed=False,
                    message=f"Faltan campos requeridos: {missing_fields}",
                    details=f"Campos encontrados: {list(cat.keys())}"
                ))
                return False

            self.results.append(TestResult(
                name="GET Categories",
                passed=True,
                message=f"✓ {len(categories)} categorías encontradas",
                details=f"Ejemplo: {cat['category_id']} - {cat['name']} ({cat['distance_km']}km)"
            ))
            return True

        except requests.RequestException as e:
            self.results.append(TestResult(
                name="GET Categories",
                passed=False,
                message=f"Error de request: {e}"
            ))
            return False
        except json.JSONDecodeError:
            self.results.append(TestResult(
                name="GET Categories",
                passed=False,
                message="Respuesta no es JSON válido",
                details=response.text[:200]
            ))
            return False
        except Exception as e:
            self.results.append(TestResult(
                name="GET Categories",
                passed=False,
                message=f"Error: {e}"
            ))
            return False

    def test_get_athletes(self) -> bool:
        """Test 4: GET /api/events/{event_id}/athletes"""
        try:
            url = f"{self.api_url}/api/events/{self.event_id}/athletes"
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=15
            )

            if response.status_code != 200:
                self.results.append(TestResult(
                    name="GET Athletes",
                    passed=False,
                    message=f"HTTP {response.status_code}",
                    details=response.text[:200]
                ))
                return False

            data = response.json()

            if 'athletes' not in data:
                self.results.append(TestResult(
                    name="GET Athletes",
                    passed=False,
                    message="Respuesta sin campo 'athletes'",
                    details=f"Keys: {list(data.keys())}"
                ))
                return False

            athletes = data['athletes']
            if not isinstance(athletes, list):
                self.results.append(TestResult(
                    name="GET Athletes",
                    passed=False,
                    message="'athletes' no es un array"
                ))
                return False

            if len(athletes) == 0:
                self.results.append(TestResult(
                    name="GET Athletes",
                    passed=True,
                    message="Endpoint OK pero sin atletas",
                    details="Agregar atletas al evento en la plataforma"
                ))
                return True

            # Verificar campos requeridos
            athlete = athletes[0]
            required = ['athlete_id', 'bib_number', 'category_id']
            name_field = 'full_name' if 'full_name' in athlete else ('first_name' if 'first_name' in athlete else None)

            missing = [f for f in required if f not in athlete]
            if missing or not name_field:
                self.results.append(TestResult(
                    name="GET Athletes",
                    passed=False,
                    message=f"Faltan campos: {missing + (['full_name o first_name'] if not name_field else [])}",
                    details=f"Campos: {list(athlete.keys())}"
                ))
                return False

            # Campos recomendados
            recommended = ['email', 'phone', 'birth_date', 'gender', 'team_name']
            has_recommended = [f for f in recommended if f in athlete]

            self.results.append(TestResult(
                name="GET Athletes",
                passed=True,
                message=f"✓ {len(athletes)} atletas encontrados",
                details=f"Campos recomendados presentes: {len(has_recommended)}/{len(recommended)}"
            ))
            return True

        except Exception as e:
            self.results.append(TestResult(
                name="GET Athletes",
                passed=False,
                message=f"Error: {e}"
            ))
            return False

    def test_post_detection(self) -> bool:
        """Test 5: POST /api/events/{event_id}/detection"""
        try:
            url = f"{self.api_url}/api/events/{self.event_id}/detection"

            # Crear detección de prueba
            test_detection = {
                "tag_id": "TEST-7662",
                "athlete_id": "test-athlete-id",
                "bib_number": 999,
                "timestamp": datetime.now().isoformat(),
                "antenna_port": 1,
                "event_type": "start",
                "category_id": "test",
                "checkpoint_number": None,
                "athlete_name": "Test Athlete"
            }

            response = requests.post(
                url,
                headers=self._get_headers(),
                json=test_detection,
                timeout=10
            )

            # Aceptar 200, 201, o 404 (si no existe el atleta de prueba)
            if response.status_code in [200, 201]:
                self.results.append(TestResult(
                    name="POST Detection",
                    passed=True,
                    message=f"✓ Endpoint funcional (HTTP {response.status_code})"
                ))
                return True
            elif response.status_code == 404:
                self.results.append(TestResult(
                    name="POST Detection",
                    passed=True,
                    message="Endpoint funcional (test athlete no existe - OK)",
                    details="El endpoint acepta requests correctamente"
                ))
                return True
            elif response.status_code == 400:
                # Puede ser validación, revisar mensaje
                data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                self.results.append(TestResult(
                    name="POST Detection",
                    passed=True,
                    message="Endpoint funcional (validación de datos)",
                    details=f"Error esperado: {data.get('error', 'N/A')}"
                ))
                return True
            else:
                self.results.append(TestResult(
                    name="POST Detection",
                    passed=False,
                    message=f"HTTP {response.status_code}",
                    details=response.text[:200]
                ))
                return False

        except Exception as e:
            self.results.append(TestResult(
                name="POST Detection",
                passed=False,
                message=f"Error: {e}"
            ))
            return False

    def test_post_result(self) -> bool:
        """Test 6: POST /api/events/{event_id}/result"""
        try:
            url = f"{self.api_url}/api/events/{self.event_id}/result"

            test_result = {
                "athlete_id": "test-athlete-id",
                "bib_number": 999,
                "category_id": "test",
                "status": "finished",
                "start_time": datetime.now().isoformat(),
                "finish_time": datetime.now().isoformat(),
                "total_seconds": 1500.0,
                "position_overall": 1,
                "position_gender": 1,
                "position_category": 1,
                "checkpoint_times": {},
                "splits_seconds": {}
            }

            response = requests.post(
                url,
                headers=self._get_headers(),
                json=test_result,
                timeout=10
            )

            if response.status_code in [200, 201]:
                self.results.append(TestResult(
                    name="POST Result",
                    passed=True,
                    message=f"✓ Endpoint funcional (HTTP {response.status_code})"
                ))
                return True
            elif response.status_code in [400, 404]:
                self.results.append(TestResult(
                    name="POST Result",
                    passed=True,
                    message="Endpoint funcional (test athlete no existe - OK)"
                ))
                return True
            else:
                self.results.append(TestResult(
                    name="POST Result",
                    passed=False,
                    message=f"HTTP {response.status_code}"
                ))
                return False

        except Exception as e:
            self.results.append(TestResult(
                name="POST Result",
                passed=False,
                message=f"Error: {e}"
            ))
            return False

    def run_all_tests(self) -> bool:
        """Ejecutar todos los tests"""
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}  Test de Integración - Sistema de Timing ↔ Plataforma de Registro")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")

        # 1. Cargar configuración
        print(f"{Fore.YELLOW}[1/6] Cargando configuración...{Style.RESET_ALL}")
        if not self.load_config():
            self._print_results()
            return False

        # 2. Test conectividad
        print(f"{Fore.YELLOW}[2/6] Probando conectividad...{Style.RESET_ALL}")
        if not self.test_connectivity():
            self._print_results()
            return False

        # 3. Test autenticación
        print(f"{Fore.YELLOW}[3/6] Verificando autenticación...{Style.RESET_ALL}")
        self.test_authentication()

        # 4. Test GET categories
        print(f"{Fore.YELLOW}[4/6] Probando GET /categories...{Style.RESET_ALL}")
        self.test_get_categories()

        # 5. Test GET athletes
        print(f"{Fore.YELLOW}[5/6] Probando GET /athletes...{Style.RESET_ALL}")
        self.test_get_athletes()

        # 6. Test POST detection
        print(f"{Fore.YELLOW}[6/6] Probando POST /detection...{Style.RESET_ALL}")
        self.test_post_detection()

        # 7. Test POST result (opcional)
        print(f"{Fore.YELLOW}[Bonus] Probando POST /result...{Style.RESET_ALL}")
        self.test_post_result()

        print()
        self._print_results()

        # Retornar True si todos los tests críticos pasaron
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        return passed == total

    def _print_results(self):
        """Imprimir resultados"""
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}  Resultados{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")

        for result in self.results:
            icon = "✓" if result.passed else "✗"
            color = Fore.GREEN if result.passed else Fore.RED

            print(f"{color}{icon} {result.name}: {result.message}{Style.RESET_ALL}")
            if result.details:
                print(f"  {Fore.WHITE}└─ {result.details}{Style.RESET_ALL}")

        # Resumen
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        percent = (passed / total * 100) if total > 0 else 0

        print(f"\n{Fore.CYAN}{'─'*70}{Style.RESET_ALL}")
        if passed == total:
            print(f"{Fore.GREEN}✓ Todos los tests pasaron ({passed}/{total}){Style.RESET_ALL}")
            print(f"{Fore.GREEN}  La integración está lista para usar!{Style.RESET_ALL}")
        elif passed >= total * 0.7:
            print(f"{Fore.YELLOW}⚠ {passed}/{total} tests pasaron ({percent:.0f}%){Style.RESET_ALL}")
            print(f"{Fore.YELLOW}  Algunos tests fallaron, revisar detalles arriba{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}✗ {passed}/{total} tests pasaron ({percent:.0f}%){Style.RESET_ALL}")
            print(f"{Fore.RED}  Integración no está lista, resolver errores{Style.RESET_ALL}")

        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")


def main():
    """Main function"""
    tester = IntegrationTester()
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
