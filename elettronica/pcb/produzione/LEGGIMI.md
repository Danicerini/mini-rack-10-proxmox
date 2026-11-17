# PCB plancia: file per JLCPCB (14/11/2026)

Scheda 70 x 47 mm (14/11). Prima di ordinare, stampa la scheda 1:1 e controlla che la distanza tra le file di pin dell'ESP sia 25,4 mm.

## Versione THT (`tht/`): la saldi tutta tu
- Su jlcpcb.com carica `gerber_tht.zip`. Le impostazioni standard vanno bene: 2 strati, 1,6 mm, HASL, 5 pezzi.
- La lista dei pezzi da saldare è in `da_saldare_a_mano.csv`: 2 x 74HC595 DIP-16, 10 resistenze da 220 ohm, 2 condensatori da 100 nF, 2 da 10 uF, 2 file da 15 pin femmina, connettori JST-XH da 8, 4, 4, 4, 11, 5 e 3 pin.

## Versione SMD (`smd/`): JLCPCB monta chip, resistenze e condensatori
- Carica `gerber_smd.zip`, attiva "PCB Assembly" (Economic, lato Top) e carica `BOM_JLC.csv` e `CPL_JLC.csv`.
- **Nell'anteprima di JLC controlla che il pallino del pin 1 dei 74HC595 sia nel verso giusto**: a volte la rotazione va corretta di 180 gradi.
- A mano restano solo i pin femmina e i connettori JST-XH (`da_saldare_a_mano.csv`).

## Costi indicativi (prezzi a memoria, NON letti dal sito: il preventivo vero lo dà jlcpcb.com)
| | THT | SMD |
|---|---|---|
| 5 schede nude | circa 2-5 $ | circa 2-5 $ |
| Montaggio (2 schede montate, avvio + stencil + saldature) | - | circa 10-15 $ |
| Componenti montati da JLC | - | circa 1-2 $ |
| Componenti da comprare tu (595, resistenze, condensatori) | circa 3-6 EUR | - |
| JST-XH + pin femmina (in tutte e due) | circa 5-10 EUR | circa 5-10 EUR |
| Spedizione in Italia + IVA 22% | circa 8-20 $ | circa 8-20 $ |
| **Totale indicativo** | **circa 20-35 EUR** | **circa 30-50 EUR** |
