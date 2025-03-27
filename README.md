# Mini PCS

Este projeto foi desenvolvido para facilitar a configuração de TV Boxes através do ADB, permitindo alterar DPI, desinstalar aplicativos e reiniciar dispositivos de forma automatizada.

## Funcionalidades

- Interface gráfica moderna e intuitiva usando CustomTkinter
- Conexão automática ao dispositivo via ADB
- Gerenciamento de aplicativos:
  - Lista predefinida de apps comuns para remoção
  - Visualização de todos os apps instalados no dispositivo
  - Seleção múltipla de apps para remoção
  - Checkbox para apps padrão
- Configuração de DPI:
  - Campo personalizável para definir o DPI desejado
  - Valor padrão de 160 DPI
  - Exibição do DPI atual do dispositivo
- Informações do dispositivo:
  - Modelo do dispositivo
  - Versão do Android
  - DPI atual
- Salvamento automático das últimas configurações:
  - Último IP utilizado
  - Último valor de DPI
- Atalhos:
  - Tecla Enter para executar a ação principal
- Links rápidos:
  - Acesso ao perfil do LinkedIn do desenvolvedor
  - Acesso ao repositório GitHub do projeto

## Pré-requisitos

- Python 3.x instalado
- Bibliotecas necessárias:

```bash
pip install customtkinter pillow
```

- O executável ADB está incluso no projeto para uso direto

## Como usar

1. Clone este repositório:

```bash
git clone https://github.com/ruafernd/minipcs.git
```

2. Navegue até o diretório do projeto:

```bash
cd minipcs
```

3. Execute o programa:

```bash
python configurardpi.py
```

4. Na interface do programa:
   - Digite o IP do dispositivo (geralmente começa com 10.0.0.)
   - Defina o DPI desejado (padrão: 160)
   - Clique em "Conectar" para verificar o dispositivo
   - Selecione os aplicativos que deseja remover
   - Clique em "Alterar DPI e Remover Apps" ou pressione Enter

## Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para enviar pull requests ou relatar problemas.

## Autor

Desenvolvido por [Ruã Fernandes](https://www.linkedin.com/in/ruã-fernandes-araújo-4617a8282/)

## Licença

Este projeto é licenciado sob a [MIT License](LICENSE).

## Versão

v4.0
