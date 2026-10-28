//+------------------------------------------------------------------+
//| Yasuke.mq5 : niveaux des stratégies du bot sur un graphique MT5.  |
//| Reprend les règles de indicateurs/yasuke.pine (TradingView), sans |
//| W3 ni Double 7. Ce n'est pas un signal du bot : les vrais signaux |
//| restent ceux de Telegram. Graphiques conseillés :                 |
//|   Nasdaq (NAS100) en 5 min  -> zone de bruit + VWAP               |
//|   Bitcoin (BTCUSD) en 5 à 60 min -> cassure Williams, Donchian 1 h|
//|   Or (XAUUSD+) en 5 à 60 min -> nuit asiatique                    |
//+------------------------------------------------------------------+
#property copyright "Yasuke"
#property version   "1.00"
#property indicator_chart_window
#property indicator_buffers 10
#property indicator_plots   10

#property indicator_label1  "Zone de bruit haute"
#property indicator_type1   DRAW_LINE
#property indicator_color1  clrTeal
#property indicator_label2  "Zone de bruit basse"
#property indicator_type2   DRAW_LINE
#property indicator_color2  clrTeal
#property indicator_label3  "VWAP du jour"
#property indicator_type3   DRAW_LINE
#property indicator_color3  clrOrange
#property indicator_label4  "Williams : niveau d'achat"
#property indicator_type4   DRAW_LINE
#property indicator_color4  clrLimeGreen
#property indicator_width4  2
#property indicator_label5  "Williams : stop (ouverture UTC)"
#property indicator_type5   DRAW_LINE
#property indicator_color5  clrTomato
#property indicator_label6  "Donchian 1 h : haut 20"
#property indicator_type6   DRAW_LINE
#property indicator_color6  clrDodgerBlue
#property indicator_label7  "Donchian 1 h : bas 20"
#property indicator_type7   DRAW_LINE
#property indicator_color7  clrDodgerBlue
#property indicator_label8  "Nuit asiatique : stop 1 %"
#property indicator_type8   DRAW_LINE
#property indicator_color8  clrRed
#property indicator_label9  "Achat"
#property indicator_type9   DRAW_ARROW
#property indicator_color9  clrLime
#property indicator_width9  2
#property indicator_label10 "Vente"
#property indicator_type10  DRAW_ARROW
#property indicator_color10 clrRed
#property indicator_width10 2

enum StratMode { MODE_AUTO = 0, MODE_NQ = 1, MODE_BTC = 2, MODE_GOLD = 3 };

input StratMode Mode         = MODE_AUTO; // Stratégie (Auto : selon le symbole)
input int       MaxBars      = 5000;      // Nombre de bougies calculées
input int       ServerMinusNY = 7;        // Heures entre l'heure du serveur et New York (7 chez Vantage)

#define SLOTS 78   // bougies 5 min de 9:30 à 16:00 New York
#define LOOK  14   // jours de moyenne de la zone de bruit

double ZbUp[], ZbLo[], Vwap[], WilLvl[], WilStop[], DonHi[], DonLo[], GoldStop[], BuyArr[], SellArr[];

int      g_mode = MODE_NQ;
datetime g_lastRun = 0;

//+------------------------------------------------------------------+
int ResolveMode()
  {
   if(Mode != MODE_AUTO)
      return((int)Mode);
   string t = _Symbol;
   StringToUpper(t);
   if(StringFind(t, "BTC") >= 0)
      return(MODE_BTC);
   if(StringFind(t, "XAU") >= 0 || StringFind(t, "GOLD") >= 0)
      return(MODE_GOLD);
   return(MODE_NQ);
  }

//+------------------------------------------------------------------+
int OnInit()
  {
   g_mode = ResolveMode();
   SetIndexBuffer(0, ZbUp, INDICATOR_DATA);
   SetIndexBuffer(1, ZbLo, INDICATOR_DATA);
   SetIndexBuffer(2, Vwap, INDICATOR_DATA);
   SetIndexBuffer(3, WilLvl, INDICATOR_DATA);
   SetIndexBuffer(4, WilStop, INDICATOR_DATA);
   SetIndexBuffer(5, DonHi, INDICATOR_DATA);
   SetIndexBuffer(6, DonLo, INDICATOR_DATA);
   SetIndexBuffer(7, GoldStop, INDICATOR_DATA);
   SetIndexBuffer(8, BuyArr, INDICATOR_DATA);
   SetIndexBuffer(9, SellArr, INDICATOR_DATA);
   for(int p = 0; p < 10; p++)
      PlotIndexSetDouble(p, PLOT_EMPTY_VALUE, EMPTY_VALUE);
   PlotIndexSetInteger(8, PLOT_ARROW, 233);   // flèche vers le haut
   PlotIndexSetInteger(9, PLOT_ARROW, 234);   // flèche vers le bas
   PlotIndexSetInteger(8, PLOT_ARROW_SHIFT, 12);
   PlotIndexSetInteger(9, PLOT_ARROW_SHIFT, -12);
   IndicatorSetString(INDICATOR_SHORTNAME, "Yasuke");
   return(INIT_SUCCEEDED);
  }

//+------------------------------------------------------------------+
void Clear(const int from, const int total)
  {
   for(int i = from; i < total; i++)
     {
      ZbUp[i] = EMPTY_VALUE; ZbLo[i] = EMPTY_VALUE; Vwap[i] = EMPTY_VALUE;
      WilLvl[i] = EMPTY_VALUE; WilStop[i] = EMPTY_VALUE; DonHi[i] = EMPTY_VALUE; DonLo[i] = EMPTY_VALUE;
      GoldStop[i] = EMPTY_VALUE; BuyArr[i] = EMPTY_VALUE; SellArr[i] = EMPTY_VALUE;
     }
  }

//+------------------------------------------------------------------+
//| Zone de bruit v2 (Nasdaq 5 min) : bornes = max/min(ouverture 9:30,|
//| clôture de la veille) +/- moyenne sur 14 jours du mouvement depuis|
//| l'ouverture à la même heure. Décision aux demi-heures de 10:00 à  |
//| 15:30 : clôture hors des bornes = achat (haut) ou vente (bas).   |
//+------------------------------------------------------------------+
void CalcNasdaq(const int start, const int total, const datetime &time[], const double &open[],
                const double &high[], const double &low[], const double &close[], const long &vol[])
  {
   int maxDays = MaxBars / 60 + LOOK + 5;       // 78 bougies par séance : large marge
   double vals[];
   ArrayResize(vals, maxDays * SLOTS);
   ArrayInitialize(vals, -1.0);
   int dIdx = -1;
   double dOpen = 0, pClose = 0, lastRth = 0, pv = 0, vv = 0;
   bool haveClose = false, signalDone = false;
   for(int i = start; i < total; i++)
     {
      datetime ny = time[i] - ServerMinusNY * 3600;
      int minDay = (int)((ny % 86400) / 60);
      bool inRth = (minDay >= 570 && minDay <= 955);
      if(!inRth)
         continue;
      if(minDay == 570)
        {
         if(dIdx >= maxDays - 1)
            break;
         dIdx++;
         dOpen = open[i];
         pClose = lastRth;
         haveClose = (lastRth > 0);
         pv = 0; vv = 0; signalDone = false;
        }
      if(dIdx < 0)
         continue;
      int slot = (minDay - 570) / 5;
      double v = (double)MathMax(vol[i], 1);
      pv += (high[i] + low[i] + close[i]) / 3.0 * v;
      vv += v;
      Vwap[i] = pv / vv;
      vals[dIdx * SLOTS + slot] = MathAbs(close[i] / dOpen - 1.0);
      if(dIdx >= LOOK && haveClose)
        {
         double s = 0; int n = 0;
         for(int d = dIdx - LOOK; d < dIdx; d++)
           {
            double x = vals[d * SLOTS + slot];
            if(x >= 0) { s += x; n++; }
           }
         if(n >= LOOK / 2)
           {
            double sig = s / n;
            double ub = MathMax(dOpen, pClose) * (1.0 + sig);
            double lb = MathMin(dOpen, pClose) * (1.0 - sig);
            ZbUp[i] = ub;
            ZbLo[i] = lb;
            int closeMin = minDay + 5;
            if(!signalDone && closeMin % 30 == 0 && closeMin >= 600 && closeMin <= 930)
              {
               if(close[i] > ub) { BuyArr[i] = low[i]; signalDone = true; }
               else if(close[i] < lb) { SellArr[i] = high[i]; signalDone = true; }
              }
           }
        }
      lastRth = close[i];
     }
  }

//+------------------------------------------------------------------+
//| Bitcoin : cassure Williams (jour UTC) et canal Donchian 1 h.     |
//+------------------------------------------------------------------+
void CalcBitcoin(const int start, const int total, const datetime &time[], const double &open[],
                 const double &high[], const double &low[])
  {
   long off = (long)(TimeTradeServer() - TimeGMT());
   off = (off / 1800) * 1800;
   double wHi = 0, wLo = 0, wOpen = 0, wPrev = 0;
   bool wDone = false, haveDay = false, havePrev = false;
   long curDay = -1;
   for(int i = start; i < total; i++)
     {
      long utc = (long)time[i] - off;
      long day = utc / 86400;
      if(day != curDay)
        {
         if(haveDay)
           {
            wPrev = wHi - wLo;
            havePrev = true;
           }
         curDay = day;
         wHi = high[i]; wLo = low[i]; wOpen = open[i];
         wDone = false; haveDay = true;
        }
      else
        {
         wHi = MathMax(wHi, high[i]);
         wLo = MathMin(wLo, low[i]);
        }
      if(havePrev)
        {
         double lvl = wOpen + 0.5 * wPrev;
         WilLvl[i] = lvl;
         WilStop[i] = wOpen;
         if(!wDone && high[i] >= lvl)
           {
            wDone = true;
            BuyArr[i] = low[i];
           }
        }
      // Donchian 1 h : plus haut / plus bas des 20 bougies 1 h avant la bougie 1 h en cours
      if(PeriodSeconds(_Period) <= 3600)
        {
         int sh = iBarShift(_Symbol, PERIOD_H1, time[i], false);
         if(sh >= 0)
           {
            int ih = iHighest(_Symbol, PERIOD_H1, MODE_HIGH, 20, sh + 1);
            int il = iLowest(_Symbol, PERIOD_H1, MODE_LOW, 20, sh + 1);
            if(ih >= 0 && il >= 0)
              {
               DonHi[i] = iHigh(_Symbol, PERIOD_H1, ih);
               DonLo[i] = iLow(_Symbol, PERIOD_H1, il);
              }
           }
        }
     }
  }

//+------------------------------------------------------------------+
//| Or : nuit asiatique. Du lundi au jeudi, achat à l'ouverture de   |
//| 18:00 New York, vente à 03:00, stop 1 % sous l'entrée.            |
//+------------------------------------------------------------------+
void CalcGold(const int start, const int total, const datetime &time[], const double &open[],
              const double &low[])
  {
   bool inPos = false;
   double stop = 0;
   int prevHour = -1;
   for(int i = start; i < total; i++)
     {
      datetime ny = time[i] - ServerMinusNY * 3600;
      int hour = (int)((ny % 86400) / 3600);
      int dow = (int)(((long)ny / 86400 + 4) % 7);       // 0 = dimanche
      if(inPos && hour == 3 && prevHour != 3)
        {
         SellArr[i] = open[i];
         inPos = false;
        }
      if(!inPos && hour == 18 && prevHour != 18 && dow >= 1 && dow <= 4)
        {
         inPos = true;
         stop = open[i] * 0.99;
         BuyArr[i] = low[i];
        }
      if(inPos && low[i] <= stop)
        {
         SellArr[i] = stop;
         inPos = false;
        }
      if(inPos)
         GoldStop[i] = stop;
      prevHour = hour;
     }
  }

//+------------------------------------------------------------------+
int OnCalculate(const int rates_total, const int prev_calculated, const datetime &time[],
                const double &open[], const double &high[], const double &low[], const double &close[],
                const long &tick_volume[], const long &volume[], const int &spread[])
  {
   if(rates_total < 50)
      return(0);
   // pas plus d'un recalcul toutes les 3 s tant qu'aucune nouvelle bougie n'est arrivée
   if(prev_calculated > 0 && prev_calculated == rates_total && TimeLocal() - g_lastRun < 3)
      return(rates_total);
   g_lastRun = TimeLocal();
   int start = MathMax(0, rates_total - MaxBars);
   Clear(0, rates_total);
   if(g_mode == MODE_NQ)
      CalcNasdaq(start, rates_total, time, open, high, low, close, tick_volume);
   else if(g_mode == MODE_BTC)
      CalcBitcoin(start, rates_total, time, open, high, low);
   else
      CalcGold(start, rates_total, time, open, low);
   return(rates_total);
  }
//+------------------------------------------------------------------+
