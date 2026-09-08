import json
import os
import urllib.request
from PyQt5.QtCore import QSettings, QThread, Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class AIWorkerThread(QThread):
    """
    Thread assíncrona para requisições à API da IA (Gemini ou OpenAI) sem travar a interface.
    """
    response_received = pyqtSignal(bool, str, str)

    def __init__(self, provider: str, model_name: str, api_key: str, prompt: str, context: str = "", parent=None):
        super().__init__(parent)
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key
        self.prompt = prompt
        self.context = context

    def run(self):
        try:
            if "Gemini" in self.provider:
                text = self._call_gemini()
            else:
                text = self._call_openai()
            
            self.response_received.emit(True, text, "")
        except Exception as e:
            self.response_received.emit(False, "", str(e))

    def _call_gemini(self) -> str:
        api_key_clean = self.api_key.strip()
        if not api_key_clean:
            raise Exception("Chave de API (API Key) não informada.")

        full_prompt = (
            "Você é um assistente especializado em edição e revisão acadêmica em Markdown.\n"
            "Sua tarefa é executar a INSTRUÇÃO DO USUÁRIO aplicando-a sobre o CONTEXTO DO DOCUMENTO fornecido abaixo.\n"
            "MUITO IMPORTANTE: Retorne APENAS o texto revisado/processado final em Markdown, sem saudações, introduções ou explicações adicionais.\n\n"
        )
        if self.context:
            full_prompt += f"=== CONTEXTO DO DOCUMENTO DO USUÁRIO ===\n{self.context}\n=== FIM DO CONTEXTO ===\n\n"
        
        full_prompt += f"=== INSTRUÇÃO DO USUÁRIO ===\n{self.prompt}\n"
        if self.context:
            full_prompt += "\nAplique a instrução acima sobre o CONTEXTO DO DOCUMENTO DO USUÁRIO fornecido acima."

        # 1. Tentar utilizar a SDK oficial google-genai (mesma utilizada no digital-twin-ecossistemas)
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key_clean)
            
            # Consulta dinâmica de modelos ativos na conta/chave do usuário
            dynamic_models = []
            try:
                for m in client.models.list():
                    m_name = getattr(m, 'name', '') or str(m)
                    clean_name = m_name.replace("models/", "")
                    if "gemini" in clean_name and not any(x in clean_name for x in ["embed", "imagen", "bidi", "audio", "tts"]):
                        dynamic_models.append(clean_name)
            except Exception:
                pass

            # Lista padrão de fallbacks atualizados
            fallback_models = [
                'gemini-2.5-flash',
                'gemini-2.0-flash',
                'gemini-1.5-flash-latest',
                'gemini-1.5-flash',
                'gemini-2.0-flash-lite'
            ]

            # Unir dinâmica com fallbacks mantendo ordem
            model_candidates = []
            for m in dynamic_models + fallback_models:
                if m not in model_candidates:
                    model_candidates.append(m)

            # Se o usuário selecionou um específico no combo, coloca no topo
            selected_model = "gemini-1.5-flash"
            if "2.0 Flash" in self.model_name:
                selected_model = "gemini-2.0-flash"
            elif "1.5 Pro" in self.model_name:
                selected_model = "gemini-1.5-pro"

            if selected_model in model_candidates:
                model_candidates.remove(selected_model)
            model_candidates.insert(0, selected_model)

            last_sdk_err = None
            gen_config = types.GenerateContentConfig(
                temperature=0.7,
            )

            for m_name in model_candidates:
                try:
                    response = client.models.generate_content(
                        model=m_name,
                        contents=full_prompt,
                        config=gen_config
                    )
                    if response and response.text:
                        return response.text.strip()
                except Exception as e:
                    last_sdk_err = e
                    continue

            if last_sdk_err:
                err_str = str(last_sdk_err)
                if "API_KEY_INVALID" in err_str or "API key not valid" in err_str:
                    raise Exception("A Chave de API (API Key) do Gemini é inválida. Por favor, cole uma chave válida obtida no Google AI Studio (https://aistudio.google.com/).")
                raise Exception(f"Erro na resposta da API Gemini: {err_str}")

        except Exception as sdk_err:
            if "API Key" in str(sdk_err) or "API_KEY_INVALID" in str(sdk_err) or "Gemini" in str(sdk_err):
                raise sdk_err

        # Fallback HTTP caso a biblioteca google-genai não esteja instalada
        base_model = "gemini-1.5-flash"
        if "2.0 Flash" in self.model_name:
            base_model = "gemini-2.0-flash"
        elif "1.5 Pro" in self.model_name:
            base_model = "gemini-1.5-pro"

        models_to_try = [base_model, "gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}]
        }
        data = json.dumps(payload).encode("utf-8")

        last_error_details = ""
        for current_model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}:generateContent?key={api_key_clean}"
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    candidates = res_data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
            except urllib.error.HTTPError as http_err:
                try:
                    err_text = http_err.read().decode("utf-8")
                    err_json = json.loads(err_text)
                    msg = err_json.get("error", {}).get("message", err_text)
                except Exception:
                    msg = str(http_err)
                last_error_details = f"HTTP {http_err.code}: {msg}"
                if "API key not valid" in msg or "API_KEY_INVALID" in msg:
                    raise Exception("A Chave de API (API Key) do Gemini é inválida. Por favor, verifique a chave copiada no Google AI Studio.")
                continue

        raise Exception(f"Não foi possível conectar com a API do Gemini.\nDetalhes: {last_error_details}")

    def _call_openai(self) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        
        model_id = "gpt-4o-mini"
        if "GPT-4o Mini" in self.model_name:
            model_id = "gpt-4o-mini"
        elif "GPT-4o" in self.model_name:
            model_id = "gpt-4o"

        messages = [
            {
                "role": "system",
                "content": "Você é um assistente especialista em escrita e edição acadêmica em Markdown. Forneça apenas o texto pronto para inserção no documento."
            }
        ]
        
        if self.context:
            messages.append({
                "role": "system",
                "content": f"Contexto do documento atual:\n{self.context}"
            })
            
        messages.append({"role": "user", "content": self.prompt})
        
        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": 0.7
        }
        
        data = json.dumps(payload).encode("utf-8")
        api_key_clean = self.api_key.strip()
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key_clean}"
            }
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                choices = res_data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
                raise Exception("Resposta da API OpenAI não continha escolhas válidas.")
        except urllib.error.HTTPError as http_err:
            try:
                err_text = http_err.read().decode("utf-8")
                err_json = json.loads(err_text)
                msg = err_json.get("error", {}).get("message", err_text)
            except Exception:
                msg = str(http_err)

            if http_err.code in (401, 403):
                raise Exception(f"Chave da API OpenAI inválida ou não autorizada:\n{msg}")
            raise Exception(f"Erro na API OpenAI (HTTP {http_err.code}): {msg}")


class AISettingsDialog(QDialog):
    """
    Diálogo moderno para configuração de provedor, modelo e chave de API da IA.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações de IA & Chaves de API")
        self.setMinimumWidth(450)
        self.settings = QSettings("LatexMDown", "AIAssistant")
        self.test_thread = None

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Grupo: Provedor e Modelo
        provider_group = QGroupBox("🤖 Provedor e Modelo de IA", self)
        provider_layout = QVBoxLayout(provider_group)
        provider_layout.setSpacing(8)

        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Provedor:", self))
        self.combo_provider = QComboBox(self)
        self.combo_provider.addItems(["Gemini (Google)", "OpenAI (GPT)"])
        h1.addWidget(self.combo_provider, 1)
        provider_layout.addLayout(h1)

        h2 = QHBoxLayout()
        h2.addWidget(QLabel("Modelo:", self))
        self.combo_model = QComboBox(self)
        h2.addWidget(self.combo_model, 1)
        provider_layout.addLayout(h2)

        layout.addWidget(provider_group)

        # Grupo: Chave de API
        key_group = QGroupBox("🔑 Chave de Acesso (API Key)", self)
        key_layout = QVBoxLayout(key_group)
        key_layout.setSpacing(8)

        h3 = QHBoxLayout()
        self.input_key = QLineEdit(self)
        self.input_key.setEchoMode(QLineEdit.Password)
        self.input_key.setPlaceholderText("Cole sua chave de API aqui...")
        h3.addWidget(self.input_key, 1)

        self.btn_toggle_key = QPushButton("👁️", self)
        self.btn_toggle_key.setFixedWidth(36)
        self.btn_toggle_key.setToolTip("Exibir/Ocultar chave")
        self.btn_toggle_key.clicked.connect(self.toggle_key_visibility)
        h3.addWidget(self.btn_toggle_key)
        key_layout.addLayout(h3)

        self.lbl_help = QLabel(
            "<small style='color: #64748B;'>Para o <b>Gemini</b>, obtenha uma chave gratuita em: "
            "<a href='https://aistudio.google.com/'>Google AI Studio</a>.<br>"
            "Para o <b>OpenAI</b>, obtenha em: "
            "<a href='https://platform.openai.com/api-keys'>OpenAI Platform</a>.</small>",
            self
        )
        self.lbl_help.setOpenExternalLinks(True)
        key_layout.addWidget(self.lbl_help)

        layout.addWidget(key_group)

        # Teste de conexão
        test_layout = QHBoxLayout()
        self.btn_test = QPushButton("🔌 Testar Conexão com a API", self)
        self.btn_test.setStyleSheet("padding: 6px 12px; font-weight: 500;")
        self.btn_test.clicked.connect(self.test_connection)
        test_layout.addWidget(self.btn_test)

        self.lbl_test_status = QLabel("", self)
        test_layout.addWidget(self.lbl_test_status, 1)
        layout.addLayout(test_layout)

        # Botões de confirmação (Salvar / Cancelar)
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, self)
        button_box.button(QDialogButtonBox.Save).setText("Salvar Configurações")
        button_box.button(QDialogButtonBox.Cancel).setText("Cancelar")
        button_box.accepted.connect(self.save_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Conexões e carregamento de valores salvos
        self.combo_provider.currentTextChanged.connect(self.update_model_list)
        self.load_settings()

    def update_model_list(self, provider_text: str):
        self.combo_model.blockSignals(True)
        self.combo_model.clear()
        if "Gemini" in provider_text:
            self.combo_model.addItems([
                "Gemini 2.5 Flash (Mais recente e rápido)",
                "Gemini 2.0 Flash",
                "Gemini 1.5 Flash",
                "Gemini 1.5 Pro"
            ])
        else:
            self.combo_model.addItems([
                "GPT-4o Mini (Recomendado)",
                "GPT-4o"
            ])
        self.combo_model.blockSignals(False)

    def toggle_key_visibility(self):
        if self.input_key.echoMode() == QLineEdit.Password:
            self.input_key.setEchoMode(QLineEdit.Normal)
        else:
            self.input_key.setEchoMode(QLineEdit.Password)

    def load_settings(self):
        saved_provider = self.settings.value("provider", "Gemini (Google)")
        saved_model = self.settings.value("model_name", "")
        saved_key = self.settings.value("api_key", "")

        self.combo_provider.setCurrentText(saved_provider)
        self.update_model_list(saved_provider)
        if saved_model:
            self.combo_model.setCurrentText(saved_model)
        if saved_key:
            self.input_key.setText(saved_key)

    def save_and_accept(self):
        self.settings.setValue("provider", self.combo_provider.currentText())
        self.settings.setValue("model_name", self.combo_model.currentText())
        self.settings.setValue("api_key", self.input_key.text().strip())
        self.accept()

    def test_connection(self):
        api_key = self.input_key.text().strip()
        if not api_key:
            QMessageBox.warning(self, "Chave Ausente", "Insira a chave de API antes de testar a conexão.")
            return

        provider = self.combo_provider.currentText()
        model_name = self.combo_model.currentText()

        self.btn_test.setEnabled(False)
        self.lbl_test_status.setText("⏳ Testando conexão...")
        self.lbl_test_status.setStyleSheet("color: #2563EB; font-weight: bold;")

        self.test_thread = AIWorkerThread(
            provider=provider,
            model_name=model_name,
            api_key=api_key,
            prompt="Responda apenas a palavra 'CONECTADO'.",
            context="",
            parent=self
        )
        self.test_thread.response_received.connect(self.on_test_finished)
        self.test_thread.start()

    def on_test_finished(self, success: bool, text: str, error_msg: str):
        self.btn_test.setEnabled(True)
        if success:
            self.lbl_test_status.setText("✓ Conexão bem-sucedida!")
            self.lbl_test_status.setStyleSheet("color: #166534; font-weight: bold;")
        else:
            clean_err = error_msg[:120] + "..." if len(error_msg) > 120 else error_msg
            self.lbl_test_status.setText(f"❌ Erro: {clean_err}")
            self.lbl_test_status.setStyleSheet("color: #DC2626; font-weight: bold;")


class AIAssistantWidget(QWidget):
    """
    Painel compacto do Assistente de IA para geração, reescrita e edição direta do arquivo Markdown.
    Projetado para encaixar harmoniosamente abaixo da árvore de arquivos na barra lateral esquerda.
    """
    apply_action = pyqtSignal(str, str)

    def __init__(self, editor_ref=None, parent=None):
        super().__init__(parent)
        self.editor_ref = editor_ref
        self.settings = QSettings("LatexMDown", "AIAssistant")
        self.ai_thread = None

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(6, 6, 6, 6)
        self.layout.setSpacing(6)

        # Cabeçalho com título
        self.header_label = QLabel("✨ Assistente IA", self)
        self.header_label.setStyleSheet("font-weight: bold; font-size: 10.5pt; color: #1E293B; padding: 2px 0px;")
        self.layout.addWidget(self.header_label)

        # Presets Rápidos de Edição (compactos)
        preset_box = QGroupBox("💡 Ações Rápidas", self)
        preset_box.setStyleSheet("QGroupBox { font-size: 8.5pt; font-weight: bold; color: #475569; }")
        preset_layout = QVBoxLayout(preset_box)
        preset_layout.setContentsMargins(4, 6, 4, 4)
        preset_layout.setSpacing(3)

        btn_preset1 = QPushButton("📝 Tom Acadêmico", self)
        btn_preset1.setToolTip("Reescreve o texto com tom formal e acadêmico")
        btn_preset1.setStyleSheet("text-align: left; padding: 4px 8px; font-size: 8.5pt;")
        btn_preset1.clicked.connect(lambda: self.set_prompt("Reescreva e aprimore o texto utilizando um tom acadêmico formal e claro, mantendo a formatação Markdown."))
        preset_layout.addWidget(btn_preset1)

        btn_preset2 = QPushButton("🔍 Ortografia & Sintaxe", self)
        btn_preset2.setToolTip("Corrige erros gramaticais, pontuação e sintaxe")
        btn_preset2.setStyleSheet("text-align: left; padding: 4px 8px; font-size: 8.5pt;")
        btn_preset2.clicked.connect(lambda: self.set_prompt("Corrija eventuais erros ortográficos, gramaticais e de pontuação mantendo o conteúdo e a estrutura Markdown."))
        preset_layout.addWidget(btn_preset2)

        btn_preset3 = QPushButton("🌐 Traduzir (Abstract)", self)
        btn_preset3.setToolTip("Traduz para inglês acadêmico técnico")
        btn_preset3.setStyleSheet("text-align: left; padding: 4px 8px; font-size: 8.5pt;")
        btn_preset3.clicked.connect(lambda: self.set_prompt("Traduza o texto para o inglês acadêmico com terminologia técnica precisa e vocabulário formal."))
        preset_layout.addWidget(btn_preset3)

        self.layout.addWidget(preset_box)

        # Campo de Instrução do Usuário
        self.label_prompt = QLabel("Instrução:", self)
        self.label_prompt.setStyleSheet("font-size: 8.5pt; font-weight: 600; color: #334155;")
        self.layout.addWidget(self.label_prompt)

        self.text_prompt = QTextEdit(self)
        self.text_prompt.setPlaceholderText("Ex: Reescreva com mais concisão acadêmica...")
        self.text_prompt.setMaximumHeight(65)
        self.text_prompt.setStyleSheet("font-size: 9pt;")
        self.layout.addWidget(self.text_prompt)

        self.chk_auto_apply = QCheckBox("⚡ Auto-aplicar no documento", self)
        self.chk_auto_apply.setChecked(False)
        self.chk_auto_apply.setStyleSheet("font-size: 8.5pt; color: #475569;")
        self.chk_auto_apply.setToolTip("Substitui automaticamente o texto após a resposta da IA.")
        self.layout.addWidget(self.chk_auto_apply)

        # Botão Principal de Geração
        self.btn_generate = QPushButton("✨ Executar Edição por IA", self)
        self.btn_generate.setCursor(Qt.PointingHandCursor)
        self.btn_generate.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: white;
                font-weight: bold;
                font-size: 9pt;
                padding: 6px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
        """)
        self.btn_generate.clicked.connect(self.generate_ai_text)
        self.layout.addWidget(self.btn_generate)

        # Resultado Gerado
        self.label_result = QLabel("Resultado Gerado:", self)
        self.label_result.setStyleSheet("font-size: 8.5pt; font-weight: 600; color: #334155;")
        self.layout.addWidget(self.label_result)

        self.text_result = QPlainTextEdit(self)
        self.text_result.setPlaceholderText("O texto gerado aparecerá aqui...")
        self.text_result.setStyleSheet("background-color: #FFFFFF; color: #1E293B; font-size: 9pt;")
        self.layout.addWidget(self.text_result, 1)

        # Ações de Aplicação no Editor
        actions_box = QGroupBox("📌 Aplicar no Editor", self)
        actions_box.setStyleSheet("QGroupBox { font-size: 8.5pt; font-weight: bold; color: #475569; }")
        actions_layout = QVBoxLayout(actions_box)
        actions_layout.setContentsMargins(4, 6, 4, 4)
        actions_layout.setSpacing(3)

        btn_insert_cursor = QPushButton("📥 Inserir no Cursor", self)
        btn_insert_cursor.setStyleSheet("background-color: #166534; color: white; font-weight: 500; padding: 4px; font-size: 8.5pt; border-radius: 3px;")
        btn_insert_cursor.clicked.connect(lambda: self.apply_to_editor("cursor"))
        actions_layout.addWidget(btn_insert_cursor)

        btn_replace_selection = QPushButton("🔄 Substituir Seleção", self)
        btn_replace_selection.setStyleSheet("background-color: #D97706; color: white; font-weight: 500; padding: 4px; font-size: 8.5pt; border-radius: 3px;")
        btn_replace_selection.clicked.connect(lambda: self.apply_to_editor("replace_selection"))
        actions_layout.addWidget(btn_replace_selection)

        btn_replace_all = QPushButton("📄 Substituir Documento", self)
        btn_replace_all.setStyleSheet("background-color: #DC2626; color: white; font-weight: 500; padding: 4px; font-size: 8.5pt; border-radius: 3px;")
        btn_replace_all.clicked.connect(lambda: self.apply_to_editor("replace_document"))
        actions_layout.addWidget(btn_replace_all)

        self.layout.addWidget(actions_box)

    def get_active_editor(self):
        """Retorna o editor ativo no momento, seja por referência direta ou callable."""
        if callable(self.editor_ref):
            return self.editor_ref()
        return self.editor_ref

    def open_settings_dialog(self):
        """Abre o diálogo de configurações da API e modelos de IA."""
        dlg = AISettingsDialog(self)
        dlg.exec_()

    def set_prompt(self, text: str):
        self.text_prompt.setPlainText(text)

    def generate_ai_text(self):
        api_key = self.settings.value("api_key", "")
        if not api_key:
            ans = QMessageBox.question(
                self,
                "Chave de API Não Configurada",
                "Você ainda não configurou uma Chave de API (API Key) para a IA.\n\nDeseja abrir as configurações agora para cadastrar sua chave?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if ans == QMessageBox.Yes:
                self.open_settings_dialog()
            return

        prompt = self.text_prompt.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Instrução Vazia", "Por favor, digite uma instrução de edição.")
            return

        editor = self.get_active_editor()
        context = ""
        if editor:
            cursor = editor.textCursor()
            if cursor.hasSelection():
                raw_sel = cursor.selectedText().replace('\u2029', '\n')
                context = f"TEXTO SELECIONADO NO EDITOR:\n{raw_sel}"
            else:
                raw_text = editor.toPlainText()
                if "!include " in raw_text or "<!-- include " in raw_text:
                    try:
                        import os
                        from app.compiler import resolve_includes
                        root_dir = os.getcwd()
                        main_win = self.window()
                        if hasattr(main_win, 'project_root_dir'):
                            root_dir = main_win.project_root_dir
                        context = resolve_includes(raw_text, root_dir)
                    except Exception:
                        context = raw_text
                else:
                    context = raw_text

                if len(context) > 12000:
                    context = context[:12000] + "\n...[conteúdo truncado]"

        provider = self.settings.value("provider", "Gemini (Google)")
        model_name = self.settings.value("model_name", "Gemini 2.5 Flash")

        self.btn_generate.setEnabled(False)
        self.btn_generate.setText("⏳ Processando...")
        self.text_result.setPlainText("Aguardando resposta da IA...")

        self.ai_thread = AIWorkerThread(provider, model_name, api_key, prompt, context, parent=self)
        self.ai_thread.response_received.connect(self.on_ai_response)
        self.ai_thread.start()

    def on_ai_response(self, success: bool, text: str, error_msg: str):
        self.btn_generate.setEnabled(True)
        self.btn_generate.setText("✨ Executar Edição por IA")

        if success:
            self.text_result.setPlainText(text)
            if hasattr(self, 'chk_auto_apply') and self.chk_auto_apply.isChecked():
                editor = self.get_active_editor()
                if editor and editor.textCursor().hasSelection():
                    self.apply_to_editor("replace_selection")
                else:
                    self.apply_to_editor("replace_document")
        else:
            QMessageBox.critical(self, "Erro na Chamada da IA", f"Não foi possível processar a edição:\n{error_msg}")
            self.text_result.setPlainText(f"Erro: {error_msg}")

    def apply_to_editor(self, mode: str):
        text = self.text_result.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "Sem Conteúdo", "Não há texto gerado para aplicar.")
            return

        self.apply_action.emit(text, mode)

