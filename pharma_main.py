from playwright.sync_api import sync_playwright
import time
import re #regex
import traceback
from winotify import Notification
import tkinter as tk
from tkinter import messagebox

janela = messagebox #janela pop-up para ajudar o user.

#ler item -> confirmar -> proximo... (até cobrir toda a página)
# próxima página, repete.
# vou precisar incluir a espera do login.


# INICIO DO SISTEMA #

def notificacao(titulo, mensagem, duracao):
    toast = Notification(app_id="PharmaBot", title=titulo, msg=mensagem, duration=duracao)
    toast.show()

def abrir_navegador(p):

    navegador = p.chromium.launch(headless= False, channel="chrome")
    aba = navegador.new_page()
    aba.goto("https://dpsp.pharmaconnection.com.br/conferencia/saldo") 

    janela.showinfo("Instrução", "Por favor, faça login no Pharmaconnect e gere a lista desejada. Depois pressione OK.") #user_instrução 1 

    permissao_sistema = janela.askyesnocancel("AVISO", "Começar PharmaBot?")

    if permissao_sistema is True:

        try:
            janela.showinfo("Instrução", "Lembre-se que a lista deve filtrar apenas os remédios pendentes!") #user_instrução 2
            aba.wait_for_selector("#dt_table_info", timeout= 60000) #aguarda 1 minuto 
            extracao = aba.locator("#dt_table_info").inner_text()
            total_remedios = int(re.search(r"de (\d+) registros", extracao).group(1))


            print("SISTEMA: verificando total de remédios...")
            notificacao("PharmaBot", f"Total de remédios: {total_remedios}", "short")
            print(f"PHARMACONNECT | total de remédios: {total_remedios}")

            return aba, total_remedios #retorna os valores encontrados para a a função de conferência.

        except Exception as e:
            traceback.print_exc()
            janela.showerror("Erro", "Não foi possível executar o bot. Verifique se você está logado no PharmaConnect")
            print(f"SISTEMA: erro ao localizar a lista: {e}")
            return None
        
    elif permissao_sistema is False:
        print("SISTEMA: usuário cancelou a execução do bot.")
        notificacao("PharmaBot", "Execução cancelada pelo usuário.", "short")
        return None

    elif permissao_sistema is None:
        print("SISTEMA: usuário fechou a janela de permissão.")
        return None


def conferir_remedios(aba, total_remedios):
        
        #------------------------------------#
        notificacao("PharmaBot", "Iniciando conferência...", "short")
        print("SISTEMA: iniciando conferência...")

        conferidos = 0  

        while total_remedios > conferidos:  

            print(f"SISTEMA: conferindo remédio {conferidos + 1} de {total_remedios}...")
            primeira_linha = aba.locator("table#dt_table tbody tr").first
            botao = primeira_linha.locator("a.btn-danger")
            time.sleep(3) #temporario
            botao.click()
            print("SISTEMA: botao vermelho clicado")
            aba.wait_for_selector("#modal-check", state= "visible")

            aba.wait_for_selector("#btn-check-amt-match", state= "visible")
            seta_esquerda = aba.locator("#btn-check-amt-match")
            time.sleep(3)
            seta_esquerda.click()
            print("SISTEMA: seta clicada!")

            #verifica se o valor foi atualizado
            aba.wait_for_selector("#item-check input[name='amount']") #aguarda o botao '<' aparecer

            print("SISTEMA: extraindo Armário e Sistema...")
            requerido_sistema = int(aba.locator("#item-check input[name='amount']").input_value())
            print(f"PHARMACONNECT | Quantidade requerida: {requerido_sistema}")
            #----------------------------
            quantidade_armario = int(aba.locator("#item-check input[name='amount_check']").input_value())
            print(f"PHARMACONNECT | Armario: {quantidade_armario}")

            print("SISTEMA: confirmando se Sistema bate com o Armário...") 

            if requerido_sistema == quantidade_armario:
                botao_confirmar = aba.locator("button", has_text= "confirmar") 
                botao_confirmar.click()
                botao_certeza = aba.get_by_role("button", name="SIM")
                botao_certeza.click()
                print("SISTEMA: confirmado! próximo...") #volta o loop

                conferidos += 1 #variavel confirma que mais uma linha foi conferida.


            else:
                print("SISTEMA: o Pharma falhou, tentando novamente...")

                while quantidade_armario != requerido_sistema:
                    seta_esquerda.click()
                    time.sleep(2) #é melhor trocar pra espera do playw
                    quantidade_armario = int(aba.locator("#item-check input[name='amount_check']").input_value())
                    print(f"SISTEMA: tentando de novo... armário agora: {quantidade_armario}")
        

                    botao_confirmar = aba.locator("button", has_text= "confirmar")
                    botao_confirmar.click()
                    
                    botao_certeza = aba.get_by_role("button", name="SIM")
                    botao_certeza.click()

                    print("SISTEMA: agora foi! próximo...")
                    conferidos += 1
                        
            
        #------------------------------------#

        #chamar função de conferência do produto
        #conferência_produto()


with sync_playwright() as p:
    resultado = abrir_navegador(p)
    if resultado is not None:
        aba, total_remedios = resultado
        conferir_remedios(aba, total_remedios)
    else:
        print("SISTEMA: não foi possível iniciar a conferência porque abrir_navegador retornou None.")