//+------------------------------------------------------------------+
//|                                       Robo_Abertura_WDO_Genial.mq5|
//|          Robô de Abertura do Mercado - Mini Dólar (WDO) - B3      |
//|          Corretora: Genial Investimentos - MetaTrader 5           |
//+------------------------------------------------------------------+
//|  v1.31 - Padrão 2 contínuo: cada nova vela usa a anterior       |
//|          como referência até ocorrer a entrada                    |
//|                                                                   |
//|  ESTRATÉGIA (operar somente a abertura, após o leilão das 08:55)  |
//|                                                                   |
//|  Indicadores:                                                     |
//|   - Médias móveis exponenciais 13 / 17 / 21 (60 min e diário)     |
//|   - Canais do dia anterior:                                       |
//|       PDH = máxima de ontem        SUPERIOR = PDH - 7 pts         |
//|       PDL = mínima de ontem        INFERIOR = PDL + 7 pts         |
//|   - IFR (RSI) 7                                                   |
//|                                                                   |
//|  Padrão 1: abertura entre os canais -> compra/venda no toque da   |
//|            1ª média móvel; entre as médias, usa-as como S/R.      |
//|  Padrão 2: abriu entre os canais e não tocou médias -> cada vela |
//|            usa a anterior: máxima = VENDA; mínima = COMPRA.       |
//|  Padrão 3: 1ª vela abre DENTRO do canal superior -> SELL STOP     |
//|            0,5 pt acima; dentro do canal inferior -> BUY STOP     |
//|            0,5 pt abaixo.                                         |
//|  Padrão 4: IFR. Abaixo do canal inferior: IFR 10-16 = compra      |
//|            imediata; <10 ou >16 sem tocar 16 = compra no toque da |
//|            máxima/mínima da 1ª vela na 2ª vela; >16 e chega em 16 |
//|            = compra imediata. Espelhado p/ venda (86/90) acima do |
//|            canal superior.                                        |
//|                                                                   |
//|  Alvo: 6 pontos | Stop: 10 pontos | 1 operação por dia           |
//|  Crossorder automático WDOFUT -> WDO pelo MT5 da Genial.          |
//+------------------------------------------------------------------+
#property copyright "Robo Abertura WDO - Genial Investimentos"
#property version   "1.35"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>

CTrade        trade;
CPositionInfo posInfo;

//--- Inputs gerais
input group "=== Símbolo e Ordens ==="
input string   InpSymbol       = "WDOFUT";    // Símbolo (WDO contrato vigente)
input double   InpLote         = 1.0;         // Lote por operação
input double   InpGainPts      = 6.0;         // Alvo (pontos)
input double   InpLossPts      = 10.0;        // Stop (pontos)
input double   InpOffsetCanal  = 7.0;         // Distância do canal (pontos)
input double   InpRompePts     = 0.5;         // Rompimento p/ ordens stop (pontos)
input int      InpModoCanal    = 0;           // 0=stop+fade | 1=só stop (rompe linha 7) | 2=só fade (rompe PDH/PDL)
input int      InpMagic        = 55001;       // Magic Number
input ulong    InpDeviation    = 30;          // Desvio máximo (em pontos)
input bool     InpDesenharEMA  = true;        // Desenhar médias no gráfico
input double   InpToleranciaEMA = 1.0;         // Compatibilidade Profit: zona de toque da EMA (pontos)

input group "=== IFR (RSI) ==="
input int      InpRSIPeriod    = 7;           // Período do IFR
input double   InpRSICompMin   = 10.0;        // IFR compra: limite inferior
input double   InpRSICompMax   = 16.0;        // IFR compra: limite superior
input double   InpRSIVendMin   = 86.0;        // IFR venda: limite inferior
input double   InpRSIVendMax   = 90.0;        // IFR venda: limite superior

input group "=== Janela de operação (horário de Brasília) ==="
input int      InpHoraInicio   = 9;           // Hora de início
input int      InpMinInicio    = 0;           // Minuto de início
input int      InpHoraFim      = 10;          // Hora limite (cancela pendentes)
input int      InpMinFim       = 30;          // Minuto limite

//--- Handles dos indicadores
int hEma13_H1, hEma17_H1, hEma21_H1;
int hEma13_D1, hEma17_D1, hEma21_D1;
int hRSI;

//--- Estado interno
string   gSym          = "";
int      gDigits       = 1;
double   gTickSize     = 0.5;
datetime gDiaAtual     = 0;
bool     gOperouHoje   = false;
int      gEstado       = 0;   // 0=aguardando abertura | 1=1ª vela | 2=2ª vela | 3=fim
int      gPadrao       = 0;   // 1=toque média | 2=rompimento vela | 3=stop canal | 4=IFR
int      gDirecao      = 0;   // +1=compra | -1=venda | 0=entre médias (define no toque)
bool     gAguardaVela  = false; // Padrão 4: true = pula monitoração do IFR e aguarda a vela
datetime gHoraAbertura = 0;
double   gOpenDia      = 0.0;
double   gPdh          = 0.0;
double   gPdl          = 0.0;
double   gSupInterno   = 0.0; // PDH - offset  (canal SUPERIOR)
double   gInfInterno   = 0.0; // PDL + offset  (canal INFERIOR)
double   gEmaMin       = 0.0;
double   gEmaMax       = 0.0;
double   gEmas[6];            // 13/17/21 H1 + 13/17/21 D1
double   gEmaSuporte   = 0.0; // média mais próxima abaixo/igual à abertura
double   gEmaResist    = 0.0; // média mais próxima acima/igual à abertura
double   gRSIAbertura  = 0.0;
double   gAltaVela1    = 0.0;
double   gBaixaVela1   = 0.0;
datetime gHoraVelaMonitorada = 0; // abertura da vela atual do Padrão 2/4

//+------------------------------------------------------------------+
//| Inicialização                                                     |
//+------------------------------------------------------------------+
int OnInit()
{
   gSym = InpSymbol;
   if(gSym == "") gSym = _Symbol;

   if(!SymbolSelect(gSym, true))
   {
      Print("ERRO: símbolo ", gSym, " não encontrado no Market Watch.");
      return(INIT_FAILED);
   }

   gDigits   = (int)SymbolInfoInteger(gSym, SYMBOL_DIGITS);
   gTickSize = SymbolInfoDouble(gSym, SYMBOL_TRADE_TICK_SIZE);
   if(gTickSize <= 0) gTickSize = 0.5;

   //--- Médias móveis exponenciais 13/17/21 em 60 min e diário
   hEma13_H1 = iMA(gSym, PERIOD_H1, 13, 0, MODE_EMA, PRICE_CLOSE);
   hEma17_H1 = iMA(gSym, PERIOD_H1, 17, 0, MODE_EMA, PRICE_CLOSE);
   hEma21_H1 = iMA(gSym, PERIOD_H1, 21, 0, MODE_EMA, PRICE_CLOSE);
   hEma13_D1 = iMA(gSym, PERIOD_D1, 13, 0, MODE_EMA, PRICE_CLOSE);
   hEma17_D1 = iMA(gSym, PERIOD_D1, 17, 0, MODE_EMA, PRICE_CLOSE);
   hEma21_D1 = iMA(gSym, PERIOD_D1, 21, 0, MODE_EMA, PRICE_CLOSE);
   hRSI      = iRSI(gSym, PERIOD_M5, InpRSIPeriod, PRICE_CLOSE);

   if(hEma13_H1==INVALID_HANDLE || hEma17_H1==INVALID_HANDLE || hEma21_H1==INVALID_HANDLE ||
      hEma13_D1==INVALID_HANDLE || hEma17_D1==INVALID_HANDLE || hEma21_D1==INVALID_HANDLE ||
      hRSI==INVALID_HANDLE)
   {
      Print("ERRO ao criar handles dos indicadores.");
      return(INIT_FAILED);
   }

   trade.SetExpertMagicNumber(InpMagic);
   trade.SetDeviationInPoints(InpDeviation);
   trade.SetTypeFillingBySymbol(gSym);          // usa o filling mode aceito pelo símbolo/corretora
   trade.SetAsyncMode(false);

   Print("Robô de Abertura WDO v1.35 inicializado em ", gSym,
         " | Tick=", gTickSize, " | Digits=", gDigits);
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Finalização                                                       |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   if(reason != REASON_CHARTCHANGE)
   {
      ObjectsDeleteAll(0, "RA_");
      ChartRedraw();
   }
   IndicatorRelease(hEma13_H1); IndicatorRelease(hEma17_H1); IndicatorRelease(hEma21_H1);
   IndicatorRelease(hEma13_D1); IndicatorRelease(hEma17_D1); IndicatorRelease(hEma21_D1);
   IndicatorRelease(hRSI);
}

//+------------------------------------------------------------------+
//| Reset diário                                                      |
//+------------------------------------------------------------------+
void ResetDia()
{
   gOperouHoje  = false;
   gEstado      = 0;
   gPadrao      = 0;
   gDirecao     = 0;
   gAguardaVela = false;
   gHoraAbertura= 0;
   gOpenDia     = 0.0;
   gRSIAbertura = 0.0;
   gAltaVela1   = 0.0;
   gBaixaVela1  = 0.0;
   gHoraVelaMonitorada = 0;
}

//+------------------------------------------------------------------+
//| Funções utilitárias                                               |
//+------------------------------------------------------------------+
double NormPreco(double preco)
{
   return NormalizeDouble(MathRound(preco / gTickSize) * gTickSize, gDigits);
}

double NormLote(double lote)
{
   double minV = SymbolInfoDouble(gSym, SYMBOL_VOLUME_MIN);
   double maxV = SymbolInfoDouble(gSym, SYMBOL_VOLUME_MAX);
   double step = SymbolInfoDouble(gSym, SYMBOL_VOLUME_STEP);
   if(step <= 0) step = 1.0;
   lote = MathFloor(lote / step) * step;
   return MathMin(MathMax(lote, minV), maxV);
}

//--- lê 1 elemento do buffer em um deslocamento (0 = barra atual)
bool LerBuffer(int handle, int shift, double &valor)
{
   double b[1];
   if(CopyBuffer(handle, 0, shift, 1, b) != 1) return false;
   valor = b[0];
   return true;
}

//--- médias calculadas sobre a BARRA ATUAL (shift 0), como exibidas em tempo real
//    no Profit/MT5. O valor varia a cada tick enquanto H1/D1 estão em formação.
//    Mantemos as 6 médias individualmente.
void AtualizarEMAs()
{
   LerBuffer(hEma13_H1, 0, gEmas[0]);
   LerBuffer(hEma17_H1, 0, gEmas[1]);
   LerBuffer(hEma21_H1, 0, gEmas[2]);
   LerBuffer(hEma13_D1, 0, gEmas[3]);
   LerBuffer(hEma17_D1, 0, gEmas[4]);
   LerBuffer(hEma21_D1, 0, gEmas[5]);

   gEmaMin = gEmas[0];
   gEmaMax = gEmas[0];
   for(int i=1; i<6; i++)
   {
      if(gEmas[i] < gEmaMin) gEmaMin = gEmas[i];
      if(gEmas[i] > gEmaMax) gEmaMax = gEmas[i];
   }
}

//--- seleciona as médias que realmente funcionam como primeiro suporte/resistência
//    a partir do preço de abertura. Isso evita ignorar EMAs intermediárias.
void DefinirMediasDeToque()
{
   gEmaSuporte = 0.0;
   gEmaResist  = 0.0;

   for(int i=0; i<6; i++)
   {
      double ema = gEmas[i];
      if(ema <= 0.0) continue;

      if(ema <= gOpenDia)
      {
         if(gEmaSuporte == 0.0 || ema > gEmaSuporte)
            gEmaSuporte = ema;       // mais próxima por baixo
      }

      if(ema >= gOpenDia)
      {
         if(gEmaResist == 0.0 || ema < gEmaResist)
            gEmaResist = ema;        // mais próxima por cima
      }
   }
}

double RSIAgora()
{
   double v = 0.0;
   LerBuffer(hRSI, 0, v);
   return v;
}

//--- garante que os indicadores já calcularam antes de decidir o padrão
bool DadosProntos()
{
   if(BarsCalculated(hEma13_H1) < 15 || BarsCalculated(hEma17_H1) < 19 ||
      BarsCalculated(hEma21_H1) < 23 || BarsCalculated(hEma13_D1) < 15 ||
      BarsCalculated(hEma17_D1) < 19 || BarsCalculated(hEma21_D1) < 23 ||
      BarsCalculated(hRSI) < InpRSIPeriod + 2)
      return false;

   double v;
   if(!LerBuffer(hEma13_H1, 0, v) || v <= 0) return false;
   if(!LerBuffer(hEma21_D1, 0, v) || v <= 0) return false;
   if(!LerBuffer(hRSI, 0, v)       || v <= 0) return false;
   return true;
}

bool PossuiPosicao()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(posInfo.SelectByIndex(i))
         if(posInfo.Symbol() == gSym && posInfo.Magic() == InpMagic)
            return true;
   }
   return false;
}

void CancelarPendentes()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      ulong ticket = OrderGetTicket(i);
      if(ticket == 0) continue;
      if(OrderGetString(ORDER_SYMBOL) == gSym &&
         OrderGetInteger(ORDER_MAGIC) == InpMagic)
         trade.OrderDelete(ticket);
   }
}

bool PossuiPendente()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      ulong ticket = OrderGetTicket(i);
      if(ticket == 0) continue;
      if(OrderGetString(ORDER_SYMBOL) == gSym &&
         OrderGetInteger(ORDER_MAGIC) == InpMagic)
         return true;
   }
   return false;
}

//+------------------------------------------------------------------+
//| Cálculo de PDH / PDL e canais SUPERIOR e INFERIOR                 |
//+------------------------------------------------------------------+
void CalcularNiveis()
{
   gPdh        = iHigh(gSym, PERIOD_D1, 1);   // máxima do dia anterior
   gPdl        = iLow (gSym, PERIOD_D1, 1);   // mínima do dia anterior
   gSupInterno = NormPreco(gPdh - InpOffsetCanal);  // SUPERIOR = PDH - 7
   gInfInterno = NormPreco(gPdl + InpOffsetCanal);  // INFERIOR = PDL + 7
}

//+------------------------------------------------------------------+
//| Desenho das linhas e canais no gráfico                            |
//+------------------------------------------------------------------+
void LinhaH(const string nome, double preco, color cor, int largura)
{
   if(ObjectFind(0, nome) < 0)
      ObjectCreate(0, nome, OBJ_HLINE, 0, 0, preco);
   ObjectSetDouble(0, nome, OBJPROP_PRICE, 0, preco);
   ObjectSetInteger(0, nome, OBJPROP_COLOR, cor);
   ObjectSetInteger(0, nome, OBJPROP_WIDTH, largura);
   ObjectSetInteger(0, nome, OBJPROP_STYLE, STYLE_SOLID);
   ObjectSetInteger(0, nome, OBJPROP_BACK, true);
   ObjectSetInteger(0, nome, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(0, nome, OBJPROP_HIDDEN, true);
}

void Rotulo(const string nome, datetime t, double preco, string texto, color cor)
{
   if(ObjectFind(0, nome) < 0)
      ObjectCreate(0, nome, OBJ_TEXT, 0, t, preco);
   ObjectSetInteger(0, nome, OBJPROP_TIME, 0, t);
   ObjectSetDouble(0, nome, OBJPROP_PRICE, 0, preco);
   ObjectSetString (0, nome, OBJPROP_TEXT, texto);
   ObjectSetInteger(0, nome, OBJPROP_COLOR, cor);
   ObjectSetInteger(0, nome, OBJPROP_FONTSIZE, 8);
   ObjectSetInteger(0, nome, OBJPROP_ANCHOR, ANCHOR_LEFT_LOWER);
   ObjectSetInteger(0, nome, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(0, nome, OBJPROP_HIDDEN, true);
}

void Retangulo(const string nome, double p1, double p2, color cor)
{
   datetime t1 = gDiaAtual - 3600;
   datetime t2 = gDiaAtual + 23 * 3600;
   if(ObjectFind(0, nome) < 0)
      ObjectCreate(0, nome, OBJ_RECTANGLE, 0, t1, p1, t2, p2);
   ObjectSetInteger(0, nome, OBJPROP_TIME, 0, t1);
   ObjectSetDouble(0, nome, OBJPROP_PRICE, 0, p1);
   ObjectSetInteger(0, nome, OBJPROP_TIME, 1, t2);
   ObjectSetDouble(0, nome, OBJPROP_PRICE, 1, p2);
   ObjectSetInteger(0, nome, OBJPROP_COLOR, cor);
   ObjectSetInteger(0, nome, OBJPROP_FILL, true);
   ObjectSetInteger(0, nome, OBJPROP_BACK, true);
   ObjectSetInteger(0, nome, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(0, nome, OBJPROP_HIDDEN, true);
}

void DesenharNiveis()
{
   LinhaH("RA_PDH", gPdh, clrRed, 2);
   LinhaH("RA_SUPERIOR", gSupInterno, clrOrange, 1);
   LinhaH("RA_INFERIOR", gInfInterno, clrDodgerBlue, 1);
   LinhaH("RA_PDL", gPdl, clrBlue, 2);

   Retangulo("RA_CANAL_SUP", gSupInterno, gPdh, C'255,235,215');
   Retangulo("RA_CANAL_INF", gPdl, gInfInterno, C'215,235,255');

   datetime tLabel = TimeCurrent() + 600;
   Rotulo("RA_LBL_PDH", tLabel, gPdh, "PDH (máxima ontem)", clrRed);
   Rotulo("RA_LBL_SUP", tLabel, gSupInterno, "SUPERIOR (PDH-7)", clrOrange);
   Rotulo("RA_LBL_INF", tLabel, gInfInterno, "INFERIOR (PDL+7)", clrDodgerBlue);
   Rotulo("RA_LBL_PDL", tLabel, gPdl, "PDL (mínima ontem)", clrBlue);

   ChartRedraw();
}

//+------------------------------------------------------------------+
//| Desenho das 6 médias móveis no gráfico (H1 sólidas, D1 tracejadas)|
//+------------------------------------------------------------------+
void LinhaMedia(const string nome, int handle, ENUM_TIMEFRAMES tf,
                color cor, int largura, int estilo)
{
   double v[];
   if(CopyBuffer(handle, 0, 0, 42, v) < 42) return;
   ArraySetAsSeries(v, true);
   if(v[1] <= 0) return;

   datetime tHist = iTime(gSym, tf, 40);   // extremidade esquerda (histórico)
   datetime tNow  = TimeCurrent();         // extremidade direita (agora, nível da barra atual)

   if(ObjectFind(0, nome) < 0)
      ObjectCreate(0, nome, OBJ_TREND, 0, tHist, v[40], tNow, v[0]);
   else
   {
      ObjectSetInteger(0, nome, OBJPROP_TIME,  0, tHist);
      ObjectSetDouble (0, nome, OBJPROP_PRICE, 0, v[40]);
      ObjectSetInteger(0, nome, OBJPROP_TIME,  1, tNow);
      ObjectSetDouble (0, nome, OBJPROP_PRICE, 1, v[0]);
   }
   ObjectSetInteger(0, nome, OBJPROP_COLOR, cor);
   ObjectSetInteger(0, nome, OBJPROP_WIDTH, largura);
   ObjectSetInteger(0, nome, OBJPROP_STYLE, estilo);
   ObjectSetInteger(0, nome, OBJPROP_RAY_RIGHT, false);
   ObjectSetInteger(0, nome, OBJPROP_RAY_LEFT,  false);
   ObjectSetInteger(0, nome, OBJPROP_BACK, true);
   ObjectSetInteger(0, nome, OBJPROP_SELECTABLE, false);
   ObjectSetInteger(0, nome, OBJPROP_HIDDEN, true);
}

void DesenharMedias()
{
   static datetime ultimaAtualizacao = 0;
   datetime agora = TimeCurrent();
   if(agora == ultimaAtualizacao) return;   // no máximo 1x por segundo
   ultimaAtualizacao = agora;

   if(!InpDesenharEMA) return;

   LinhaMedia("RA_E13H1", hEma13_H1, PERIOD_H1, clrYellow,     2, STYLE_SOLID);
   LinhaMedia("RA_E17H1", hEma17_H1, PERIOD_H1, clrOrange,     2, STYLE_SOLID);
   LinhaMedia("RA_E21H1", hEma21_H1, PERIOD_H1, clrRed,        2, STYLE_SOLID);
   LinhaMedia("RA_E13D1", hEma13_D1, PERIOD_D1, clrAqua,       1, STYLE_DASH);
   LinhaMedia("RA_E17D1", hEma17_D1, PERIOD_D1, clrDodgerBlue, 1, STYLE_DASH);
   LinhaMedia("RA_E21D1", hEma21_D1, PERIOD_D1, clrMagenta,    1, STYLE_DASH);

   //--- legenda no canto superior esquerdo
   if(ObjectFind(0, "RA_LEGENDA") < 0)
      ObjectCreate(0, "RA_LEGENDA", OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, "RA_LEGENDA", OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, "RA_LEGENDA", OBJPROP_XDISTANCE, 10);
   ObjectSetInteger(0, "RA_LEGENDA", OBJPROP_YDISTANCE, 18);
   ObjectSetString (0, "RA_LEGENDA", OBJPROP_TEXT,
                    "EMA H1 13/17/21 (sólidas amarelo/laranja/vermelho) | EMA D1 13/17/21 (tracejadas)");
   ObjectSetInteger(0, "RA_LEGENDA", OBJPROP_COLOR, clrWhite);
   ObjectSetInteger(0, "RA_LEGENDA", OBJPROP_FONTSIZE, 8);
   ObjectSetInteger(0, "RA_LEGENDA", OBJPROP_SELECTABLE, false);
   ObjectSetInteger(0, "RA_LEGENDA", OBJPROP_HIDDEN, true);

   ChartRedraw();
}

//+------------------------------------------------------------------+
//| Envio de ordem a mercado com alvo 6 / stop 10                     |
//+------------------------------------------------------------------+
bool EnviarMercado(int dir)
{
   if(gOperouHoje) return false;

   double preco = (dir > 0) ? SymbolInfoDouble(gSym, SYMBOL_ASK)
                            : SymbolInfoDouble(gSym, SYMBOL_BID);
   double tp = NormPreco(preco + dir * InpGainPts);
   double sl = NormPreco(preco - dir * InpLossPts);
   double lote = NormLote(InpLote);

   bool ok = false;
   if(dir > 0)
      ok = trade.Buy(lote, gSym, 0.0, sl, tp, "Robo Abertura WDO - Compra");
   else
      ok = trade.Sell(lote, gSym, 0.0, sl, tp, "Robo Abertura WDO - Venda");

   if(ok)
   {
      gOperouHoje = true;
      gEstado = 3;
      CancelarPendentes();
      double precoExec = trade.ResultPrice();
      if(precoExec <= 0.0) precoExec = preco;
      Print("OPEROU a mercado: ", (dir > 0 ? "COMPRA" : "VENDA"),
            " | preço solicitado~", NormPreco(preco),
            " | preço executado=", NormPreco(precoExec),
            " | TP=", tp, " | SL=", sl);
   }
   else
   {
      Print("FALHA na ordem a mercado: ", trade.ResultRetcodeDescription());
   }
   return ok;
}

//+------------------------------------------------------------------+
//| Padrão 3: ordens no canal com rompimento de 0,5 pt                |
//|                                                                   |
//|  Abriu DENTRO do canal SUPERIOR (entre PDH-7 e PDH) -> VENDA:     |
//|    - SELL STOP  em (PDH-7) - 0,5  -> rompe a linha interna p/     |
//|      baixo (saída do canal com momentum)                          |
//|    - SELL LIMIT em PDH + 0,5      -> rompe a máxima de ontem      |
//|      p/ cima (fade do rompimento)                                 |
//|                                                                   |
//|  Abriu DENTRO do canal INFERIOR (entre PDL e PDL+7) -> COMPRA:    |
//|    - BUY STOP  em (PDL+7) + 0,5   -> rompe a linha interna p/     |
//|      cima (saída do canal com momentum)                           |
//|    - BUY LIMIT em PDL - 0,5       -> rompe a mínima de ontem      |
//|      p/ baixo (fade do rompimento)                                |
//|                                                                   |
//|  A 1ª ordem que executar vence; a outra é cancelada na hora.      |
//+------------------------------------------------------------------+
void ColocarOrdensCanal(int dir)
{
   double precoStop=0, precoLimit=0;
   string tagStop, tagLimit;

   if(dir < 0)   // canal SUPERIOR -> vendas
   {
      precoStop  = NormPreco(gSupInterno - InpRompePts);   // (PDH-7) - 0,5
      precoLimit = NormPreco(gPdh        + InpRompePts);   // PDH + 0,5
      tagStop    = "Robo WDO - SellStop rompe (PDH-7)";
      tagLimit   = "Robo WDO - SellLimit fade PDH";
   }
   else          // canal INFERIOR -> compras
   {
      precoStop  = NormPreco(gInfInterno + InpRompePts);   // (PDL+7) + 0,5
      precoLimit = NormPreco(gPdl        - InpRompePts);   // PDL - 0,5
      tagStop    = "Robo WDO - BuyStop rompe (PDL+7)";
      tagLimit   = "Robo WDO - BuyLimit fade PDL";
   }

   double bid = SymbolInfoDouble(gSym, SYMBOL_BID);
   double ask = SymbolInfoDouble(gSym, SYMBOL_ASK);
   long stopsLevel = SymbolInfoInteger(gSym, SYMBOL_TRADE_STOPS_LEVEL);
   double minDist  = stopsLevel * SymbolInfoDouble(gSym, SYMBOL_POINT);

   //--- perna STOP: rompimento da linha interna para fora do canal
   if(InpModoCanal == 0 || InpModoCanal == 1)
   {
      double p = precoStop;
      bool valida = (dir < 0) ? (p < bid - minDist)      // sell stop abaixo do bid
                              : (p > ask + minDist);     // buy stop acima do ask
      if(valida)
      {
         double tp = NormPreco(p + dir * InpGainPts);
         double sl = NormPreco(p - dir * InpLossPts);
         bool ok = (dir < 0)
            ? trade.SellStop(NormLote(InpLote), p, gSym, sl, tp, ORDER_TIME_GTC, 0, tagStop)
            : trade.BuyStop (NormLote(InpLote), p, gSym, sl, tp, ORDER_TIME_GTC, 0, tagStop);
         Print("Padrão 3 STOP: ", (dir < 0 ? "SELL" : "BUY"), " @ ", p,
               " | TP=", tp, " SL=", sl, (ok ? " [OK]" : " [FALHA: " + trade.ResultRetcodeDescription() + "]"));
      }
      else
         Print("Padrão 3 STOP: ", p, " inválido p/ o mercado (bid=", bid,
               " ask=", ask, ") - perna ignorada");
   }

   //--- perna LIMIT: fade no rompimento de PDH/PDL
   if(InpModoCanal == 0 || InpModoCanal == 2)
   {
      double p = precoLimit;
      bool valida = (dir < 0) ? (p > ask + minDist)      // sell limit acima do ask
                              : (p < bid - minDist);     // buy limit abaixo do bid
      if(valida)
      {
         double tp = NormPreco(p + dir * InpGainPts);
         double sl = NormPreco(p - dir * InpLossPts);
         bool ok = (dir < 0)
            ? trade.SellLimit(NormLote(InpLote), p, gSym, sl, tp, ORDER_TIME_GTC, 0, tagLimit)
            : trade.BuyLimit (NormLote(InpLote), p, gSym, sl, tp, ORDER_TIME_GTC, 0, tagLimit);
         Print("Padrão 3 LIMIT: ", (dir < 0 ? "SELL" : "BUY"), " @ ", p,
               " | TP=", tp, " SL=", sl, (ok ? " [OK]" : " [FALHA: " + trade.ResultRetcodeDescription() + "]"));
      }
      else
         Print("Padrão 3 LIMIT: ", p, " inválido p/ o mercado (bid=", bid,
               " ask=", ask, ") - perna ignorada");
   }
}

//+------------------------------------------------------------------+
//| Início da sessão: decide o padrão com base no preço de abertura   |
//+------------------------------------------------------------------+
void IniciarSessao()
{
   //--- localiza a vela M5 das 09:00 mesmo que o robô tenha sido ligado depois
   datetime abertura = gDiaAtual + InpHoraInicio * 3600 + InpMinInicio * 60;
   int idx = iBarShift(gSym, PERIOD_M5, abertura, false);
   if(idx < 0) idx = 0;

   gHoraAbertura = iTime(gSym, PERIOD_M5, idx);
   gOpenDia      = iOpen (gSym, PERIOD_M5, idx);
   if(!LerBuffer(hRSI, idx, gRSIAbertura))
   {
      Print("ERRO: não foi possível ler o IFR da vela de abertura.");
      return;
   }
   AtualizarEMAs();
   DefinirMediasDeToque();

   bool primeiraVelaFechada = (iTime(gSym, PERIOD_M5, 0) > gHoraAbertura);

   if(PossuiPosicao())   // já operou (ex.: pendente do padrão 3 executou no 1º tick)
   {
      gOperouHoje = true;
      gEstado = 3;
      return;
   }

   gEstado = 1;
   Print("--- ABERTURA: ", NormPreco(gOpenDia), " | PDH=", gPdh, " PDL=", gPdl,
         " | EMAmin=", NormPreco(gEmaMin), " EMAmax=", NormPreco(gEmaMax),
         " | suporteEMA=", (gEmaSuporte>0 ? DoubleToString(NormPreco(gEmaSuporte),gDigits) : "--"),
         " resistênciaEMA=", (gEmaResist>0 ? DoubleToString(NormPreco(gEmaResist),gDigits) : "--"),
         " | IFR=", DoubleToString(gRSIAbertura, 1),
         (primeiraVelaFechada ? " | (recuperação: 1ª vela já fechada)" : ""));

   Print("EMA LIVE (shift 0) | H1: 13=", DoubleToString(gEmas[0],gDigits),
         " 17=", DoubleToString(gEmas[1],gDigits),
         " 21=", DoubleToString(gEmas[2],gDigits),
         " | D1: 13=", DoubleToString(gEmas[3],gDigits),
         " 17=", DoubleToString(gEmas[4],gDigits),
         " 21=", DoubleToString(gEmas[5],gDigits));

   //--- ACIMA do canal superior -> Padrão 4 (venda com IFR sobrecomprado)
   if(gOpenDia > gPdh)
   {
      gPadrao  = 4;
      gDirecao = -1;
      if(gRSIAbertura >= InpRSIVendMin && gRSIAbertura <= InpRSIVendMax)
         EnviarMercado(-1);                                  // IFR 86-90: venda imediata
      else if(gRSIAbertura > InpRSIVendMax)
         gAguardaVela = true;                                // IFR > 90: aguarda vela
      else
         gAguardaVela = false;                               // IFR < 86: monitora chegada em 86
   }
   //--- ABAIXO do canal inferior -> Padrão 4 (compra com IFR sobrevendido)
   else if(gOpenDia < gPdl)
   {
      gPadrao  = 4;
      gDirecao = +1;
      if(gRSIAbertura >= InpRSICompMin && gRSIAbertura <= InpRSICompMax)
      {
         Print("GATILHO P4: abaixo da PDL e IFR de abertura entre 10 e 16 -> COMPRA IMEDIATA");
         EnviarMercado(+1);
      }                                                       // IFR 10-16: compra imediata
      else if(gRSIAbertura < InpRSICompMin)
         gAguardaVela = true;                                // IFR < 10: aguarda vela
      else
         gAguardaVela = false;                               // IFR > 16: monitora chegada em 16
   }
   //--- DENTRO do canal superior [SUPERIOR, PDH] -> Padrão 3 venda
   else if(gOpenDia >= gSupInterno)
   {
      gPadrao  = 3;
      gDirecao = -1;
      ColocarOrdensCanal(-1);
   }
   //--- DENTRO do canal inferior [PDL, INFERIOR] -> Padrão 3 compra
   else if(gOpenDia <= gInfInterno)
   {
      gPadrao  = 3;
      gDirecao = +1;
      ColocarOrdensCanal(+1);
   }
   //--- ENTRE os canais -> Padrão 1 (toque das médias) com fallback para o Padrão 2
   else
   {
      gPadrao = 1;
      if(gOpenDia > gEmaMax)      gDirecao = +1;   // abriu acima de todas as médias
      else if(gOpenDia < gEmaMin) gDirecao = -1;   // abriu abaixo de todas as médias
      else                        gDirecao = 0;    // abriu entre as médias (usar como S/R)
   }

   //--- recuperação: se ligado após o fechamento da 1ª vela, usa a vela
   //    imediatamente anterior à atual como referência. No Padrão 2,
   //    essa referência continuará avançando vela a vela até a entrada.
   if(primeiraVelaFechada && gEstado == 1)
   {
      gAltaVela1  = iHigh(gSym, PERIOD_M5, 1);
      gBaixaVela1 = iLow (gSym, PERIOD_M5, 1);
      gHoraVelaMonitorada = iTime(gSym, PERIOD_M5, 0);
      if(gPadrao == 1) gPadrao = 2;   // janela de toque das médias passou -> Padrão 2
      gEstado = 2;
      Print("Recuperação: referência atualizada para a vela anterior. Alta=",
            gAltaVela1, " Baixa=", gBaixaVela1);
   }
}

//+------------------------------------------------------------------+
//| Processamento durante a 1ª vela de 5 minutos                      |
//+------------------------------------------------------------------+
void ProcessarPrimeiraVela()
{
   // Atualiza as EMAs H1/D1 em tempo real a cada tick para que o gatilho
   // use o mesmo valor dinâmico visualizado no Profit.
   AtualizarEMAs();
   DefinirMediasDeToque();

   double alta  = iHigh(gSym, PERIOD_M5, 0);
   double baixa = iLow (gSym, PERIOD_M5, 0);

   //--- Padrão 1: toque da PRIMEIRA média pelo PREÇO EXECUTÁVEL.
   //    IMPORTANTE: não usamos mais máxima/mínima acumulada da vela nem
   //    tolerância de 1 tick. Isso evitava que o gatilho disparasse antes
   //    do preço realmente negociável tocar a média e, na compra, ainda
   //    somasse o spread até o ASK.
   //
   //    COMPRA: dispara quando o ASK atual toca/cruza a EMA de suporte.
   //    VENDA : dispara quando o BID atual toca/cruza a EMA de resistência.
   //
   //    A EMA é normalizada para o tick válido do WDO, pois o valor matemático
   //    da média pode ficar entre dois preços negociáveis (ex.: 5132,27).
   if(gPadrao == 1)
   {
      MqlTick tick;
      if(!SymbolInfoTick(gSym, tick))
      {
         Print("ERRO: não foi possível obter o tick atual para o toque da EMA.");
         return;
      }

      double ask = tick.ask;
      double bid = tick.bid;
      double emaSupExec = (gEmaSuporte > 0.0 ? NormPreco(gEmaSuporte) : 0.0);
      double emaResExec = (gEmaResist  > 0.0 ? NormPreco(gEmaResist)  : 0.0);

      // Zona de compatibilidade com o Profit. Em alguns pregões o histórico/feed
      // do MT5 gera uma EMA ligeiramente deslocada em relação ao Profit.
      // Para não perder o toque visual do Profit, consideramos tocada a média
      // quando o preço executável entra a até InpToleranciaEMA pontos dela.
      double tolEMA = MathMax(0.0, InpToleranciaEMA);
      double gatilhoCompra = (emaSupExec > 0.0 ? emaSupExec + tolEMA : 0.0);
      double gatilhoVenda  = (emaResExec > 0.0 ? emaResExec - tolEMA : 0.0);

      if(gDirecao > 0)
      {
         if(gatilhoCompra > 0.0 && ask <= gatilhoCompra)
         {
            Print("TOQUE/ZONA EMA COMPRA A MERCADO: ASK=", DoubleToString(ask,gDigits),
                  " | EMA MT5=", DoubleToString(emaSupExec,gDigits),
                  " | limite Profit=", DoubleToString(gatilhoCompra,gDigits),
                  " | tolerância=", DoubleToString(tolEMA,1),
                  " | BID=", DoubleToString(bid,gDigits));
            EnviarMercado(+1);
         }
      }
      else if(gDirecao < 0)
      {
         if(gatilhoVenda > 0.0 && bid >= gatilhoVenda)
         {
            Print("TOQUE/ZONA EMA VENDA A MERCADO: BID=", DoubleToString(bid,gDigits),
                  " | EMA MT5=", DoubleToString(emaResExec,gDigits),
                  " | limite Profit=", DoubleToString(gatilhoVenda,gDigits),
                  " | tolerância=", DoubleToString(tolEMA,1),
                  " | ASK=", DoubleToString(ask,gDigits));
            EnviarMercado(-1);
         }
      }
      else
      {
         // Entre as médias, usa a mesma zona de compatibilidade em ambos os lados.
         bool tocouSup = (gatilhoCompra > 0.0 && ask <= gatilhoCompra);
         bool tocouRes = (gatilhoVenda  > 0.0 && bid >= gatilhoVenda);

         if(tocouSup && tocouRes)
         {
            // Situação rara (spread/EMAs muito próximas): prioriza a referência
            // mais próxima do preço de abertura, mantendo a regra anterior.
            double dSup = MathAbs(gOpenDia - emaSupExec);
            double dRes = MathAbs(emaResExec - gOpenDia);
            if(dSup <= dRes)
            {
               Print("TOQUE DUPLO EMA -> COMPRA A MERCADO | ASK=", ask,
                     " EMA MT5=", emaSupExec, " limite=", gatilhoCompra);
               EnviarMercado(+1);
            }
            else
            {
               Print("TOQUE DUPLO EMA -> VENDA A MERCADO | BID=", bid,
                     " EMA MT5=", emaResExec, " limite=", gatilhoVenda);
               EnviarMercado(-1);
            }
         }
         else if(tocouSup)
         {
            Print("TOQUE/ZONA EMA COMPRA A MERCADO: ASK=", DoubleToString(ask,gDigits),
                  " | EMA MT5=", DoubleToString(emaSupExec,gDigits),
                  " | limite Profit=", DoubleToString(gatilhoCompra,gDigits),
                  " | BID=", DoubleToString(bid,gDigits));
            EnviarMercado(+1);
         }
         else if(tocouRes)
         {
            Print("TOQUE/ZONA EMA VENDA A MERCADO: BID=", DoubleToString(bid,gDigits),
                  " | EMA MT5=", DoubleToString(emaResExec,gDigits),
                  " | limite Profit=", DoubleToString(gatilhoVenda,gDigits),
                  " | ASK=", DoubleToString(ask,gDigits));
            EnviarMercado(-1);
         }
      }
      return;
   }

   //--- Padrão 4: IFR.
   //    IMPORTANTE: se o IFR DA ABERTURA já estiver na faixa imediata
   //    (10..16 para compra / 86..90 para venda), continuamos tentando
   //    a ordem a mercado enquanto estivermos na 1ª vela e ainda não
   //    houver operação. Isso evita perder a entrada quando a primeira
   //    tentativa é recusada/transitoriamente indisponível no 1º tick.
   if(gPadrao == 4)
   {
      double rsi = RSIAgora();

      if(gDirecao > 0)
      {
         // Abriu abaixo da PDL com IFR entre 10 e 16 = COMPRA IMEDIATA.
         if(gRSIAbertura >= InpRSICompMin && gRSIAbertura <= InpRSICompMax)
         {
            Print("PADRÃO 4 COMPRA IMEDIATA: IFR abertura=",
                  DoubleToString(gRSIAbertura,2),
                  " faixa [", DoubleToString(InpRSICompMin,1),
                  ",", DoubleToString(InpRSICompMax,1), "]");
            EnviarMercado(+1);
            return;
         }

         // Abriu acima de 16: compra assim que o IFR chegar a 16.
         if(!gAguardaVela && gRSIAbertura > InpRSICompMax && rsi <= InpRSICompMax)
         {
            Print("PADRÃO 4: IFR caiu até 16. RSI atual=", DoubleToString(rsi,2));
            EnviarMercado(+1);
            return;
         }
      }
      else if(gDirecao < 0)
      {
         // Regra espelhada: IFR de abertura entre 86 e 90 = VENDA IMEDIATA.
         if(gRSIAbertura >= InpRSIVendMin && gRSIAbertura <= InpRSIVendMax)
         {
            Print("PADRÃO 4 VENDA IMEDIATA: IFR abertura=",
                  DoubleToString(gRSIAbertura,2),
                  " faixa [", DoubleToString(InpRSIVendMin,1),
                  ",", DoubleToString(InpRSIVendMax,1), "]");
            EnviarMercado(-1);
            return;
         }

         // Abriu abaixo de 86: venda assim que o IFR chegar a 86.
         if(!gAguardaVela && gRSIAbertura < InpRSIVendMin && rsi >= InpRSIVendMin)
         {
            Print("PADRÃO 4: IFR subiu até 86. RSI atual=", DoubleToString(rsi,2));
            EnviarMercado(-1);
            return;
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Processamento do Padrão 2/4 após a primeira vela                 |
//+------------------------------------------------------------------+
void ProcessarVelaSeguinte()
{
   double alta  = iHigh(gSym, PERIOD_M5, 0);
   double baixa = iLow (gSym, PERIOD_M5, 0);

   //--- Padrão 2: toca/rompe a mínima da vela anterior = COMPRA; máxima = VENDA
   if(gPadrao == 2)
   {
      if(baixa <= gBaixaVela1)      EnviarMercado(+1);
      else if(alta >= gAltaVela1)   EnviarMercado(-1);
      return;
   }

   //--- Padrão 4 (casos de espera): mantém a lógica original usando a referência vigente
   if(gPadrao == 4)
   {
      if(baixa <= gBaixaVela1 || alta >= gAltaVela1)
         EnviarMercado(gDirecao);
   }
}

//+------------------------------------------------------------------+
//| Tick principal                                                    |
//+------------------------------------------------------------------+
void OnTick()
{
   //--- novo dia: reset, recalcula PDH/PDL e redesenha canais
   datetime dia = iTime(gSym, PERIOD_D1, 0);
   if(dia != gDiaAtual)
   {
      gDiaAtual = dia;
      ResetDia();
      CalcularNiveis();
      DesenharNiveis();
   }

   //--- mantém as 6 médias desenhadas no gráfico (atualização 1x/segundo)
   DesenharMedias();

   datetime agora     = TimeCurrent();
   datetime abertura  = gDiaAtual + InpHoraInicio * 3600 + InpMinInicio * 60;
   datetime fimJanela = gDiaAtual + InpHoraFim    * 3600 + InpMinFim    * 60;

   //--- fim da janela: cancela pendentes e encerra o dia
   if(agora >= fimJanela)
   {
      if(gEstado != 3 || PossuiPendente())
      {
         CancelarPendentes();
         gEstado = 3;
      }
      return;
   }

   if(gOperouHoje) return;

   //--- posição aberta (ex.: stop do padrão 3 executou): encerra e cancela pendentes
   if(gEstado >= 1 && PossuiPosicao())
   {
      gOperouHoje = true;
      gEstado = 3;
      CancelarPendentes();
      Print("Posição detectada. Robô encerrado para hoje (1 operação/dia).");
      return;
   }

   //--- início da sessão: 1º tick a partir do horário configurado
   if(gEstado == 0 && agora >= abertura)
   {
      //--- TRAVA DE DADOS: só decide o padrão quando os indicadores estiverem prontos.
      //    Sem isso, o robô decidia com médias zeradas e nunca registrava o toque.
      if(!DadosProntos())
      {
         static datetime ultimoAviso = 0;
         if(agora - ultimoAviso >= 10)
         {
            Print("Aguardando dados dos indicadores (médias/IFR) carregarem...");
            ultimoAviso = agora;
         }
         return;
      }
      IniciarSessao();
   }

   if(gEstado == 1)
   {
      ProcessarPrimeiraVela();
      if(gOperouHoje) return;

      //--- transição: fechamento da 1ª vela -> abertura da 2ª
      datetime tAtual = iTime(gSym, PERIOD_M5, 0);
      if(tAtual > gHoraAbertura)
      {
         gAltaVela1  = iHigh(gSym, PERIOD_M5, 1);
         gBaixaVela1 = iLow (gSym, PERIOD_M5, 1);
         gHoraVelaMonitorada = tAtual;

         if(gPadrao == 1) gPadrao = 2;   // não tocou médias na 1ª vela -> Padrão 2
         gEstado = 2;
         Print("2ª vela aberta. Referência = 1ª vela | Alta=", gAltaVela1,
               " Baixa=", gBaixaVela1);
      }
   }
   else if(gEstado == 2)
   {
      // No Padrão 2, se a vela atual terminar sem tocar a máxima ou a
      // mínima da referência, a vela que acabou de fechar vira a nova
      // referência para a próxima. Ex.: V2 usa V1; V3 usa V2; V4 usa V3...
      datetime tAtual = iTime(gSym, PERIOD_M5, 0);
      if(gPadrao == 2 && gHoraVelaMonitorada > 0 && tAtual > gHoraVelaMonitorada)
      {
         gAltaVela1  = iHigh(gSym, PERIOD_M5, 1);
         gBaixaVela1 = iLow (gSym, PERIOD_M5, 1);
         gHoraVelaMonitorada = tAtual;
         Print("Padrão 2: nova vela de referência | Alta=", gAltaVela1,
               " Baixa=", gBaixaVela1,
               " | aguardando COMPRA na mínima ou VENDA na máxima.");
      }

      ProcessarVelaSeguinte();
   }
}
//+------------------------------------------------------------------+
