* VERSIE Start 19/09/2019
* Dr. R. BEUNIS
* NucPuC simulatie programma versie VFP 9.0

&& Gebruik van RAND(-1) (neemt seed van de klok) geeft identieke waarden
&& als de volgende RAND(-1)'s zo snel volgen dat de klokwaarde nog niet veranderde - niet in loop gebruiken dus !!

&& RESOURCEFILES van desktop verwijderen -------------------------------------------------------------------------------------------------------
PARAMETERS plCalled,pcCMD,plReport

IF NOT plCalled
	IF NOT VERSION(2)=2
		lcPath = JUSTPATH(SET('RESOURCE',1))
		SET RESOURCE OFF
		ERASE ('&lcPath.\FOXUSER.*')
	ENDIF
	CLEAR ALL
	CLOSE ALL

	&& SYSTEEM-instellingen en instellen op directory waarin het programma ingeladen is ------------------------------------------------------------ 

	PUBLIC pcSAFETY,pcSTRICTDATE,pcROOT,plCalled,pcCMD
	plCalled=.F.

	pcSAFETY=SET('SAFETY')
	SET SAFETY OFF
	pcSTRICTDATE=SET('STRICTDATE')
	SET STRICTDATE TO 0
	SET DATE TO DMY
	SET HOURS TO 24
	SET UDFPARMS TO REFERENCE
	SET COMPATIBLE OFF
	SET TALK OFF
	SET CURSOR OFF

	pcROOT=SYS(16)
	pcROOT=LEFT(pcROOT,RAT('\',pcROOT)-1)
	&& SYS(16)=executing programma MET pad, geeft GEEN pad als .APP ! wel als .EXE of .FXP
	CD (pcRoot)
ENDIF

&& Kleuren in constanten zetten ---------------------------------------------------------------------------------------------------------------

PUBLIC pnZwart,pnLichtGrijs,pnGrijs,pnDonkerGrijs,pnWit,;
		 pnLichtRood,pnRood,pnDonkerRood,pnLichtGroen,pnGroen,pnDonkerGroen,;
		 pnLichtBlauw,pnBlauw,pnDonkerBlauw,pnGeel,pnLichtGeel,pnHalfDonkerGeel,pnDonkerGeel,;
		 pnCyaan,pnLichtCyaan,pnHalfDonkerCyaan,pnDonkerCyaan,pnMagenta,pnLichtMagenta

DO INITCOLOR

PUBLIC oNuCPuC,pnH,pnW
STORE 0 TO pnH,pnW

PUBLIC plStop,plRun,plAbort,plSlow,plDemo,plClustered
STORE .F. TO plStop,plRun,plAbort,plSlow,plDemo,plClustered

PUBLIC pnDist,pnHOffSet,pnVOffSet,pnHPosNuC,pnHPosPuC,pnRad,pnGroupSize
STORE 0 TO pnDist,pnHOffSet,pnVOffSet,pnHPosNuC,pnHPosPuC,pnRad,pnGroupSize
pnGroupSize=1

PUBLIC pcClF,pcNuC,pcNuCold,pcPuC,pcPuCreal,pcC,pcLF,pcClF_NxtG,pcClF_ActG1,pcLIM
STORE '' TO pcClF,pcNuC,pcNuCold,pcPuC,pcPuCreal,pcC,pcClF_NxtG,pcClF_ActG1,pcLIM

pcLF=CHR(13)+CHR(10)
_TOOLTIPTIMEOUT=0

	oNuCPuC=CREATEOBJECT('NUCPUC')
	oNuCPuC.Show(1)

&& Instellingen herstellen en afsluiten -------------------------------------------------------------------------------------------------------

IF NOT plCalled
	SET STRICTDATE TO &pcSTRICTDATE
	SET SAFETY &pcSAFETY
	SET TALK ON
	RELEASE ALL
	CLEAR ALL
	CLOSE ALL
ENDIF

&& Klasdefinities -----------------------------------------------------------------------------------------------------------------------------

&& COMP NUCPUC
DEFINE CLASS NUCPUC AS FORM
	WindowState		= 2
	ShowTips		= .T.
	AlwaysOnTop		= .T.
	BackColor		= pnGrijs
	FontSize		= 8
	FontBold		= .T.

	lNUCPUC			= .F.
	
	ADD OBJECT DUMMY AS EDITBOX WITH Left=-1000, Width=530, Height=520, FontSize=7, FontName="Courier New", FontSize=7, FontBold=.T., Value=''
	ADD OBJECT TXT AS EDITBOX WITH Width=530, Height=520, FontSize=7, FontName="Courier New", FontSize=7, FontBold=.T., Value='', ReadOnly=.T.
	ADD OBJECT SS AS LABEL WITH Top=250, Width=100, Height=150, Caption='', Visible=.T., BorderStyle=1, BackColor=thisform.BackColor,;
								WordWrap=.T., Alignment=2, FontName="Courier New", FontSize=7, FontBold=.T., ToolTipText="For display only."
	
	PROCEDURE Activate(nX,cAlias)
	IF thisform.lNUCPUC
		RETURN
	ENDIF
	thisform.lNUCPUC=.T.
	pnH=thisform.Height
	pnW=thisform.Width

	pnDist=40 && Distance between NuCs
	pnHOffSet=140 && Horizontal offset
	pnVOffSet=50 && Vertical offset
	pnHPosNuC=pnHOffSet+pnDist*1 && Position of NuC columnn
	pnHPosPuC=pnHOffSet+pnDist*10 && Position of PuC axon diverging point columnn
	pnRad=10 && cirkelstraal

	PUBLIC ARRAY CNP[10]
	FOR nX=1 TO 10
		CNP(nX)=REPLICATE(CHR(nX-1+48),3)
	ENDFOR
	
	FOR nX=1 TO 5
		cX=LTRIM(STR(nX))
		thisform.AddObject("CBU"+cX,"CBU",5)
	ENDFOR

	FOR nX=1 TO 2
		cX=LTRIM(STR(nX))
		thisform.AddObject("CBLU"+cX,"CBLU")
	ENDFOR

	FOR nX=1 TO 5
		cX=LTRIM(STR(nX))
		thisform.AddObject("CBLD"+cX,"CBLD")
	ENDFOR

	FOR nX=1 TO 3
		cX=LTRIM(STR(nX))
		thisform.AddObject("CBD"+cX,"CBD",3)
	ENDFOR

	FOR nX=1 TO 10
		cX=LTRIM(STR(nX))
		thisform.AddObject("CBR"+cX,"CBR")
	ENDFOR
	
	FOR nX=1 TO 5
		cX=LTRIM(STR(nX))
		thisform.AddObject("SPLB"+cX,"SPLB")
		thisform.AddObject("SP"+cX,"SP")
	ENDFOR

	thisform.TXT.Top=(pnH-thisform.TXT.Height)/2
	thisform.TXT.Left=pnW/2+(pnW/2-thisform.TXT.Width)/2

	IF plCalled
		thisform.Left=pnW/2
		thisform.Width=pnW/2
	ENDIF
	PUBLIC ARRAY SSP[10,10],SSD[10,10],SUMSSP[10],SUMSSD[10],NUCPUC[11]
	SET COMPATIBLE OFF
	STORE 0.5 TO SSP
	STORE 0.0 TO SSD
	STORE '' TO NUCPUC
	SET COMPATIBLE ON
	thisform.CBU3.Click && Clicking twice sets LTP and LTD values and dims appropriate buttons for groupsize=1
	thisform.CBU3.Click
	IF plCalled
		thisform.DEMO
	ELSE
		thisform.DORUN(10)
	ENDIF
	IF plCalled
		SET COMPATIBLE ON && Must be set ON !! or pnDoc becomes a variable 'not found' on return to the main program !!
		RETURN && !! NOT 'CANCEL' - otherwise windowtype error when restarted, and also remaining interactivity !!
	ENDIF
	RETURN

	PROCEDURE FIBERS(nClF,nClF_Act,nC,nG,nB,nClF,nNuCPos,nPuCPos,;
					 nVODClF,nVODNuC,nVODNuC_Act,nVODPuC,nVSV,;
					 nVClF,nVClF_Act,nVNuC,nVNuC_Act,nVPuC,;
					 nHMidLine,nW,cT,nH)
	DOEVENTS
	nVSV=pnVOffSet+pnDist-30
	nHMidLine=(pnHPosNuC+pnHPosPuC)/2
	nW=90 && (Half) width of PuC scrambling sector
	nH=10

	IF nClF=1
		&& Eénmalige tekening van CN-box en permanente tekstjes
		thisform.DrawWidth=5
		thisform.ForeColor=pnGroen
		thisform.FillStyle=1 && (Default) Transparent. The FillColor property is ignored.
		thisform.Box(pnHPosNuC-42,pnVOffSet+pnDist/2,pnHPosPuC+42,pnVOffSet+pnDist*11)
		thisform.ForeColor=pnZwart
		thisform.FontSize=8
		cT="Cerebellar (sub)nucleus"
		thisform.Print(cT,nHMidLine-thisform.TextWidth(cT)/2,pnVOffSet+pnDist*.5-6)
		cT="NuCs"
		thisform.Print("NuCs",pnHPosNuC-pnRad-thisform.TextWidth(cT)/2,pnVOffSet+pnDist*10+20)
		cT="Branching PuC axon terminals"
		thisform.Print(cT,pnHPosPuC-thisform.TextWidth(cT),pnVOffSet+pnDist*10+17)
		thisform.FontSize=6
		cT="Line width represents PuC-NuC synapse strength (evolving)"
		thisform.Print(cT,nHMidLine-thisform.TextWidth(cT)/2,pnVOffSet+pnDist*10+5)
	ENDIF

	&& Tienmalige tekening
	
	nVODClF=pnVOffSet+pnDist*ABS(nClF)
	nNuCPos=AT(LTRIM(STR(nClF-1)),pcNuC)
	nVODNuC=pnVOffSet+pnDist*nNuCPos
	IF nClF_Act>0
		nNuCPos_Act=AT(LTRIM(STR(nClF_Act-1)),pcNuC)
		nVODNuC_Act=pnVOffSet+pnDist*nNuCPos_Act
		nVClF_Act=nVSV-nClF_Act*3
		nVNuC_Act=nVSV-nNuCPos_Act*3
	ENDIF
	nPuCPos=AT(LTRIM(STR(nClF-1)),pcPuC)
	nVODPuC=pnVOffSet+pnDist*nPuCPos

	nVClF=nVSV-nClF*3
	nVNuC=nVSV-nNuCPos*3
	nVPuC=nVSV-nPuCPos*3

	&& Circles and numbers
	thisform.FillStyle=0 && Solid.
	thisform.DrawWidth=1
	thisform.FillColor=nC
	IF nClF_Act=0
		thisform.Circle(pnRad,pnHPosNuC-pnRad,nVODNuC) && Tekent een volle cirkel
	ELSE
		thisform.Circle(pnRad,pnHPosNuC-pnRad,nVODNuC_Act) && Tekent een volle cirkel
	ENDIF

	thisform.ForeColor=nC
	thisform.FillStyle=1 && (Default) Transparent. The FillColor property is ignored.
	thisform.DrawWidth=2
	IF nC=pnRood
		thisform.FillColor=pnGroen
		IF nClF_Act=0
			thisform.Circle(pnRad+2,pnHPosNuC-pnRad,nVODNuC) && Tekent een cirkelrand errond
		ELSE
			thisform.Circle(pnRad+2,pnHPosNuC-pnRad,nVODNuC_Act) && Tekent een cirkelrand errond
		ENDIF
	ELSE
		thisform.ForeColor=thisform.BackColor
		IF nClF_Act=0
			thisform.Circle(pnRad+2,pnHPosNuC-pnRad,nVODNuC) && Veegt de cirkelrand errond weg
		ELSE
			thisform.Circle(pnRad+2,pnHPosNuC-pnRad,nVODNuC_Act) && Veegt de cirkelrand errond weg
		ENDIF
	ENDIF
	thisform.DrawWidth=1
	thisform.FillStyle=0 && Solid.

	thisform.ForeColor=pnZwart
	thisform.FontSize=8
	thisform.Print(STR(ABS(nClF),2),pnHPosNuC-32,nVODNuC-14) && de NuCnrs
	thisform.Print(STR(ABS(nClF),2),pnHPosPuC+22,nVODPuC-14) && de PuCnrs

	&& ClF-lijnen (geel)
	thisform.ForeColor=nG
	IF nClF_Act=0
		thisform.Line(0,nVClF,10,nVClF) && Start ClF line
				thisform.Line(10,nVClF,pnHPosNuC-pnRad*9,nVNuC) && Scrambled ClF line
						 thisform.Line(pnHPosNuC-pnRad*9,nVNuC,nHMidLine-nW,nVNuC) && Continuing ClF line
						 thisform.Line(pnHPosNuC-80+(11-nNuCPos)*3,nVNuC,pnHPosNuC-80+(11-nNuCPos)*3,nVODNuC) && Vertical collateral ClF line
						 thisform.Line(pnHPosNuC-80+(11-nNuCPos)*3,nVODNuC,pnHPosNuC-pnRad*2,nVODNuC) && Horizontal collateral ClF line
	ELSE
		thisform.Line(0,nVClF_Act,10,nVClF_Act) && Start ClF line
					thisform.Line(10,nVClF_Act,pnHPosNuC-pnRad*9,nVNuC_Act) && Scrambled ClF line
								 thisform.Line(pnHPosNuC-pnRad*9,nVNuC_Act,nHMidLine-nW,nVNuC_Act) && Continuing ClF line
								 thisform.Line(pnHPosNuC-80+(11-nNuCPos_Act)*3,nVNuC_Act,pnHPosNuC-80+(11-nNuCPos_Act)*3,nVODNuC_Act) && Vertical collateral ClF line
								 thisform.Line(pnHPosNuC-80+(11-nNuCPos_Act)*3,nVODNuC_Act,pnHPosNuC-pnRad*2,nVODNuC_Act) && Horizontal collateral ClF line
	ENDIF

	&& Overgangslijnen (blauw)
	thisform.ForeColor=nB
	thisform.Line(nHMidLine-nW,nVNuC,nHMidLine+nW+1,nVPuC)

	&& Verdere PuC-lijnen (blauw)
	thisform.Line(nHMidLine+nW+1,nVPuC,pnHPosPuC+80-(11-nPuCPos)*3,nVPuC)
						 thisform.Line(pnHPosPuC+80-(11-nPuCPos)*3,nVPuC,pnHPosPuC+80-(11-nPuCPos)*3,nVODPuC)
						 thisform.Line(pnHPosPuC+80-(11-nPuCPos)*3,nVODPuC,pnHPosPuc,nVODPuC)
	RETURN

	PROCEDURE DEMO
	plDemo=.T.
	thisform.SetAll('Visible',.F.)
	plRun=.F.
	DO CASE
	CASE pcCMD="1"
		thisform.DORUN(1,1)
	CASE pcCMD="2"
		thisform.CBU4.Click
		thisform.CBU4.Visible=.T.
		thisform.DORUN(1,1)
	CASE pcCMD="3"
		thisform.CBU4.Click
		thisform.CBU4.Visible=.T.
		thisform.CBU1.Click
		thisform.CBU1.Visible=.T.
		thisform.DORUN(1,1)
	CASE pcCMD="4"
		thisform.CBU4.Click
		thisform.CBU4.Visible=.T.
		thisform.CBU1.Click
		thisform.CBU1.Visible=.T.
		plStop=.T.
		thisform.CBD1.MouseDown
	CASE pcCMD="5"
		thisform.CBU4.Click
		thisform.CBU4.Visible=.T.
		thisform.CBU1.Click
		thisform.CBU1.Visible=.T.
		plSlow=.T.
		thisform.SetAll("Visible",.T.,"CBD")
		thisform.CBD1.MouseDown
	CASE pcCMD="6"
		thisform.CBU4.Click
		thisform.CBU4.Visible=.T.
		thisform.CBU1.Click
		thisform.CBU1.Visible=.T.
		thisform.CBU3.Visible=.T.
		thisform.CBU3.Click
		plSlow=.T.
		thisform.SetAll("Visible",.T.,"CBD")
		thisform.CBD1.MouseDown
	CASE pcCMD="7"
		thisform.SetAll("Visible",.T.,"CBU")
		thisform.CBU4.Click
		thisform.CBU1.Click
		thisform.CBU2.Click
		thisform.SetAll("Visible",.T.,"CBD")
		thisform.CBD1.MouseDown
	CASE pcCMD="8"
		thisform.SetAll('Visible',.T.)
		thisform.DORUN(1,1)
	CASE pcCMD="9"
		thisform.SetAll('Visible',.T.)
		thisform.CBU4.Click
		thisform.CBU1.Click
		thisform.CBU2.Click
		thisform.SP2.Value=.5
		thisform.SP5.Value=1
		thisform.CBD1.MouseDown
	ENDCASE
	RETURN
	
	PROCEDURE DORUN(nClF_ActGLen,nTH,	nX,nClF_Act,nY,nMember,nT,nMem_ClF_ActGLen,cClF_NxtG,cClF_ActG,;
					nNuCID,nNuCPos,nPuCPos,nAvgSSP,nDW,lGroupChange,nTHLTP,nTHLTD,nSum,nTimes,nSteps,nRep)
	STORE 0 TO nX,nClF_Act,nY,nMember,nMem_ClF_ActGLen,nTimes,nSteps
	SET COMPATIBLE OFF
	STORE 0.5 TO SSP
	STORE 0.0 TO SSD
	thisform.SCRAMBLE(0)
	pcLIM=REPLICATE("0",10)
	thisform.TXT.Value=''
	thisform.SS.Caption=''
	nTHLTP=thisform.SP1.Value
	nTHLTD=thisform.SP3.Value
	lNoChange=.F.
	nSum=0
	&& Simpelweg eerst het 'netwerk' tekenen
	FOR nX=1 TO 10
		thisform.FIBERS(nX,0,(pnGroen),(pnGeel),(pnBlauw))
	ENDFOR
	thisform.ForeColor=pnZwart
	FOR nX=1 TO 10
		FOR nY=1 TO 10
			thisform.Line(pnHPosNuC,pnVOffSet+pnDist*nX,pnHPosPuC,pnVOffSet+pnDist*nY)
		ENDFOR
	ENDFOR
	IF NOT plRun
		RETURN && was alleen voor de show
	ENDIF
llPause=.F.
	thisform.ENABLECTRLS(.F.)
	thisform.CBD3.Enabled=.T.
	thisform.CBD2.FontSize=8
	thisform.CBD2.ToolTipText=''
	DO WHILE nSteps<100000
		&& elke cyclus veronderstelt een synchrone activering van een ClF groep alhoewel serieel uitgevoerd
		&& en dus worden de SUMSSP en SUMSSD berekend over de hele cyclus
 		nMem_ClF_ActGLen=nClF_ActGLen && onthouden
		nAvgSSP=0
		&& Deze loop werkt een bepaalde groep af tot ie voldoende scoort met SSP (LTP) om de volgende (kleinere) groep 'over de drempel' te krijgen.
		&& Groepsverkleining dient dan ook pas te gebeuren na beëindiging van deze cyclus
		
		DO WHILE nSteps<100000
			IF nTH=1
				IF pcLIM=REPLICATE(":",10) && ALLE NuC-PuC paren zijn verbonden met lijnen 10 dik
					EXIT
				ENDIF
			ELSE && nTH=10
				&& EXIT bij nTH=10 als 1) nAvgSSP sterk genoeg is om met een gedecrementeerde groepsize verder te kunnen OF
				&&				   als 2) als zowel de gewenste LTP, als de gewenste LTD, als het gewenst aantal loops is bereikt 
				IF nAvgSSP*(nClF_ActGLen-1)/nClF_ActGLen=>nTHLTP*3
				&& De minimum SSP is met een veilige marge in staat om met een gedecrementeerde groep verder te gaan
					EXIT
				ENDIF
				IF pcLIM=REPLICATE(":",10) AND nSum=10+(thisform.SP3.Value-thisform.SP4.Value)*9 AND nTimes=>500
				&& ALLE NuC-PuC paren zijn verbonden met lijnen 10 dik
				&& EN alle 9 andere verbindingen staan op hun minimum
				&& EN de loop werd 500x uitgevoerd
					EXIT
				ENDIF
			ENDIF
			&& Zolang er onvoldoende LTP is om met een kleinere groep ook LTP te bekomen gaan we verder met dezelfde groepsgrootte
			
			&& Bij 'one-to-one' kiezen we de 'actieve' groepsleden at random volgens type "PICKGROUPMEMBERS"
			&& Bij 'one-to-many' kiezen we at random een actief groepslid uit een 'NUCPUC-groep'
			
			&& die evenwichtig decrementeert (zie bij PROCEDURE CFRETRACT)
			nRep=thisform.SP5.Value
			&& Voor de 'one-to-many' option moet nRep minstens 5 zijn om 'failed runs' door te asymmetrische CF-activatie te vermijden
			FOR nT=nRep TO IIF("many"$thisform.CBU2.Caption,nRep*11-1,nRep)
				pcClF_NxtG="0123456789" && om te beginnen = pcCLF
				IF "many"$thisform.CBU2.Caption
					cClF_ActG=NUCPUC(INT(nT/nRep))
				ELSE
					cClF_ActG=thisform.PICKGROUPMEMBERS(nClF_ActGLen) && nClF_ActGLen CFs worden at random gekozen
				ENDIF
			
				&& Omzetting om groepen in caption van CBLD3 te kunnen tonen
				pcClF_ActG1=''
				FOR nX=1 TO nClF_ActGLen
					pcClF_ActG1=pcClF_ActG1+CHR(ASC(SUBSTR(cClF_ActG,nX,1))+1)+IIF(nX<nClF_ActGLen,',','')
					pcClF_ActG1=STRTRAN(pcClF_ActG1,':',"10")
				ENDFOR

				&& Vanaf hier 4X een (dubbele) loop)
				&& 1) Voor het berekenen vd SS-sommen van de CF-geactiveerde NuCs
				&& Als SUMSSP+SUMSSD => nTHLTP zal LTP mogelijk zijn
				&& Als SUMSSP+SUMSSD => nTHLTD zal LTD mogelijk zijn
				
				STORE 0 TO SUMSSP,SUMSSD && We resetten de sommen die de 'gelijktijdige SS impact' vertegenwoordigen
				&& We berekenen de 'hyperpolarisatielevels' (door de inbreng van alle PuC-branches van door CFs geactiveerde PuCs)		
				FOR nMember=1 TO LEN(cClF_ActG) && We gaan alle leden van de geactiveerde groep af
					nNuCID=VAL(SUBSTR(cClF_ActG,nMember,1))+1 && Het IDnr vh nMemberste lid
					nNuCPos=AT(LTRIM(STR(nNuCID-1)),pcNuC) && De plaats (het positienr van dit lid) in pcNuC
					nPuCPos=AT(LTRIM(STR(nNuCID-1)),pcPuC) && De plaats (het positienr van dit lid) in pcPuC
					FOR nY=1 TO 10
						SUMSSP(nY)=SUMSSP(nY)+SSP(nPuCPos,nY)
						&& NuC(nY) krijgt input van de nYde branch van de geactiveerde PuC(nPuCPos)
						&& berekent de SUMSS voor deze NuC als de som van de SSs van alle PuC-lijnen die erop aankomen
						SUMSSD(nY)=SUMSSD(nY)+SSD(nPuCPos,nY)
					ENDFOR
				ENDFOR

				thisform.FontSize=6
				thisform.ForeColor=pnZwart
				FOR nY=1 TO 10
					thisform.Print(STR(SUMSSP(nY)+SUMSSD(nY),5,2),pnHPosNuC-19,pnVOffSet+pnDist*nY+12) && SUMSS van deze NuC
				ENDFOR

				IF "many"$thisform.CBU2.Caption
					nAvgSSP=9999 && We gaan de minimum SUMSSP berekenen (ivm beslissing tot groupsize decrement)
					FOR nY=1 TO 10
						IF LTRIM(STR(VAL(SUBSTR(pcNuC,nY,1))))$cClF_ActG
							nAvgSSP=MIN(nAvgSSP,SUMSSP(nY))
						ENDIF
					ENDFOR
				ELSE
					nAvgSSP=0 && We gaan de gemiddelde SUMSSP berekenen (ivm beslissing tot groupsize decrement)
					nX=0
					FOR nY=1 TO 10
						IF LTRIM(STR(VAL(SUBSTR(pcNuC,nY,1))))$cClF_ActG
							nX=nX+1
							nAvgSSP=nAvgSSP+SUMSSP(nY)
						ENDIF
					ENDFOR
					nAvgSSP=nAvgSSP/nX
				ENDIF

				&& 2) Voor het tekenen vd rode geactiveerde lijnen
				IF "many"$thisform.CBU2.Caption
					nClF_Act=VAL(SUBSTR(cClF_ActG,INT(RAND()*LEN(cClF_ActG))+1,1))+1
					nClF_ActPos=AT(LTRIM(STR(nClF_Act-1)),pcNuC)
					&& igv van 'one-to-many' is dit de at random gekozen actieve ClF
				ENDIF

				FOR nMember=1 TO LEN(cClF_ActG) && cClF_ActG is de groep vd ACTIEVE CFs-NuCs-PuCs
				&& we gaan alle leden van deze actieve groep af, in volgorde van hun positie in de groep die het IDnr geeft
					nNuCID=VAL(SUBSTR(cClF_ActG,nMember,1))+1 && Het IDnr vh nMemberste lid
					nNuCPos=AT(LTRIM(STR(nNuCID-1)),pcNuC) && De plaats (het positienr van dit lid) in pcNuC
					nPuCPos=AT(LTRIM(STR(nNuCID-1)),pcPuC) && De plaats (het positienr van dit lid) in pcPuC
					&& We tekenen al de fibers in rood van CF tot NuC en PuC
					IF "many"$thisform.CBU2.Caption
						thisform.FIBERS(nNuCID,nClF_Act,(pnRood),(pnRood),(pnRood))
					ELSE
						thisform.FIBERS(nNuCID,0,(pnRood),(pnRood),(pnRood))
					ENDIF
					FOR nY=1 TO 10 && We tekenen al de fibers in rood die van een actieve PuC komen en uitwaaieren naar alle NuCs
						IF plAbort
							thisform.ABORT(nY)
							RETURN
						ENDIF
						IF thisform.CBLU1.Caption="Red"
							thisform.ForeColor=pnRood
							thisform.DrawWidth=1 &&SSP(nPuCPos,nY)+SSD(nPuCPos,nY)
							thisform.Line(pnHPosPuC,pnVOffSet+pnDist*nPuCPos,pnHPosNuC,pnVOffSet+pnDist*nY) && Rode PuC-NuC lijn
						ENDIF
						
						thisform.DrawWidth=1
						thisform.FillColor=pnGroen

						IF "many"$thisform.CBU2.Caption
							lActif= ( LTRIM(STR(VAL(SUBSTR(pcNuC,nY,1))))$cClF_ActG AND nClF_ActPos=nY )
						ELSE
							&& VAL(SUBSTR(pcNuC,nY,1)) && het IDnr van de NuC op positie nY : behoort het tot de actieve groep ?
							lActif= ( LTRIM(STR(VAL(SUBSTR(pcNuC,nY,1))))$cClF_ActG )
						ENDIF
						IF lActif && Het NuCnr behoort tot de geactiveerde groep cClF_ActG
							IF SUMSSP(nY)+SUMSSD(nY)=>nTHLTP && hyperpolarisatieniveau nodig voor LTP is bereikt
								thisform.FillColor=pnGeel
							ENDIF
						ELSE && Niet geactiveerde NuC
							IF SUMSSP(nY)+SUMSSD(nY)=>nTHLTD && hyperpolarisatieniveau nodig voor LTP is bereikt
								thisform.FillColor=pnBlauw
							ENDIF
						ENDIF

						thisform.Circle(pnRad,pnHPosNuC-pnRad,pnVOffSet+pnDist*nY) && -> volgeel, volblauw of volzwarte cirkel
						nSteps=nSteps+1
						thisform.CBD1.Caption=LTRIM(STR(nSteps))
		IF nSteps/5000=INT(nSteps/5000)
&&		llPause=.T.
		ENDIF

						IF plStop AND nY=10
							thisform.ENABLECTRLS(.T.)
							RETURN
						ENDIF
						IF plDemo AND NOT plStop AND nSteps<=10
							thisform.SLEEP(.2)
						ENDIF
						
						thisform.PAUSE12(nNucID,nY)
					ENDFOR
					IF plDemo AND nClF_ActGLen<3
						FOR nX=1 TO 100000
							DOEVENTS
						ENDFOR
					ENDIF
					thisform.PAUSE(0)
					IF plDemo AND lGroupChange AND nMember=nClF_ActGLen
						lGroupChange=.F.
						thisform.CBD2.Caption="Group size decrement : "+LTRIM(STR(nClF_ActGLen+1))+" > "+LTRIM(STR(nClF_ActGLen))
						thisform.SLEEP(1)
						IF pnGroupSize=10 AND nClF_ActGLen=2
							plSlow=.F.
						ENDIF
					ENDIF
					lGroupChange=thisform.PAUSE34(nMember,nClF_ActGLen,lGroupChange)
					IF plDemo AND NOT plStop AND nSteps<=100
						thisform.SLEEP(.4)
					ENDIF
					IF plDemo AND nSteps>100
						thisform.CBLU1.Caption="No red"
					ENDIF
					IF plSlow
						thisform.SLEEP(.05)
					ENDIF
		 			IF plDemo AND nMember=nClF_ActGLen
 					ENDIF
				ENDFOR && nMember
				IF llPause
					llPause=.F.
					WAIT WINDOW STR(nSteps)
				ENDIF
				&& Voor het registreren van de lijnverdikkingen en het aanpassen van de synapsen
				
				FOR nMember=1 TO LEN(cClF_ActG) && we gaan alle leden van de actieve groep af
					nNuCID=VAL(SUBSTR(cClF_ActG,nMember,1))+1 && Het IDnr vh nMemberste lid
					nNuCPos=AT(LTRIM(STR(nNuCID-1)),pcNuC) && De plaats (het positienr van dit lid) in pcNuC
					nPuCPos=AT(LTRIM(STR(nNuCID-1)),pcPuC) && De plaats (het positienr van dit lid) in pcPuC
					&& En nu gaan we ALLE NuCs af want die krijgen elk één geactiveerde branch van deze PuC
					&& Sommige van deze NuCs zijn ook door de CF geactiveerd, andere niet

					FOR nY=1 TO 10
						nDW=INT(SSP(nPuCPos,nY)+SSD(nPuCPos,nY)) && de huidige lijndikte van PuC(nPuCPos) naar NuC(nY)
						&& De dikte vd dikste lijn die van PuC(nPuCPos) uitwaaiert wordt geregistreerd in de string die dat van de 10 PuCs bijhoudt
						&& Als alle PuCs een branch hebben met dikte 10 zal de routine afgelopen zijn als de groupsize op 1 staat

						&& Hier gaan we bijhouden of de verbindingen tussen NuC-PuC paren (tot 10) verdikken
						IF nY=nNuCPos
&&							thisform.ForeColor=pnGeel
&&							thisform.Line(pnHPosPuC,pnVOffSet+pnDist*nPuCPos,pnHPosNuC,pnVOffSet+pnDist*nY)
							IF ASC(SUBSTR(pcLIM,nNuCPos,1))-48<nDW && Aanpassen als kleiner dan nDW
								pcLIM=STUFF(pcLIM,nNuCPos,1,CHR(nDW+48))
								&& Weergave
								thisform.CBD2.Caption=pcLIM
							ENDIF
						ENDIF
						
						&& In dit gedeelte bekijken we de synapsen
						IF "many"$thisform.CBU2.Caption
							lActif= ( LTRIM(STR(VAL(SUBSTR(pcNuC,nY,1))))$cClF_ActG AND nClF_ActPos=nY )
						ELSE
							&& VAL(SUBSTR(pcNuC,nY,1)) is het IDnr van de NuC op positie nY : behoort het tot de actieve groep ?
							lActif= ( LTRIM(STR(VAL(SUBSTR(pcNuC,nY,1))))$cClF_ActG )
						ENDIF
						IF lActif && Het NuCnr behoort tot de geactiveerde groep cClF_ActG
							IF SUMSSP(nY)+SUMSSD(nY)=>nTHLTP && Hyperpolarisatie én geactiveerd
								&& als de SUMSS van deze geactiveerde NuC de LTP-drempel overschrijdt is er voldoende hyperpolarisatie voor LTP  
								IF SSP(nPuCPos,nY)+SSD(nPuCPos,nY)<10
									SSP(nPuCPos,nY)=SSP(nPuCPos,nY)+MIN(thisform.SP2.Value,10-(SSP(nPuCPos,nY)+SSD(nPuCPos,nY))) &&.5
								ENDIF
								&& De SS (Synaps Strength) wordt verhoogd (en dat heeft pas effect op de som bij de volgende passage)
							ENDIF
						ELSE && geen CF-NuC activatie
							IF SUMSSP(nY)+SUMSSD(nY)=>nTHLTD && maar wel hyperpolarisatie
								&& als de SUMSS van deze NIET geactiveerde NuC de LTD-drempel overschrijdt is er voldoende hyperpolarisatie voor LTD 
								IF SSP(nPuCPos,nY)+SSD(nPuCPos,nY)=>nTHLTD &&1
									SSD(nPuCPos,nY)=SSD(nPuCPos,nY)-thisform.SP4.Value && 1 LTD in alle andere gevallen
								ENDIF
							ENDIF
						ENDIF
						&& Tot hier

						thisform.ForeColor=thisform.BackColor 
						thisform.DrawWidth=nDW && We wissen de lijn in dezelfde dikte als ze in 't rood was
						thisform.Line(pnHPosPuC,pnVOffSet+pnDist*nPuCPos,pnHPosNuC,pnVOffSet+pnDist*nY)

						thisform.ForeColor=pnZwart
						thisform.DrawWidth=INT(SSP(nPuCPos,nY)+SSD(nPuCPos,nY)) && We tekenen de lijn in 't zwart met de nieuwe dikte
						thisform.SLOW(nDW)
						thisform.Line(pnHPosPuC,pnVOffSet+pnDist*nPuCPos,pnHPosNuC,pnVOffSet+pnDist*nY)
					ENDFOR
					thisform.FIBERS(nNuCID,0,(pnGroen),(pnGeel),(pnBlauw)) && Fibers terug in oorspronkelijke kleur
				ENDFOR

				nSum=0 && De totale som wanneer 1 PuC branch 10 dik is en al de andere 1 = (10+9)*10=190 : dan kan gestopt worden
				&& die '1' wordt echter bepaald door de LTD stap onder de THLTD,
				&& en wanneer sommigen er nooit boven geraakten wordt naar boven gecorrigeerd
				FOR nY=1 TO 10
					nSum=nSum+MAX(thisform.SP3.Value-thisform.SP4.Value,SUMSSP(nY)+SUMSSD(nY))
				ENDFOR
				IF nSum=10+(thisform.SP3.Value-thisform.SP4.Value)*9
				&& Als die som bereikt is worden nog een extra 500 loops uitgevoerd, en starten daarom de teller
					nTimes=nTimes+1
				ENDIF
 			ENDFOR
 		ENDDO
		IF "many"$thisform.CBU2.Caption AND nClF_ActGLen>1
			thisform.CFRETRACT(nClF_ActGLen)
		ENDIF
		nClF_ActGLen=MAX(0,nClF_ActGLen-1) && decrementeren maar niet onder 1
		lGroupChange=.T.
		IF nClF_ActGLen=0
			EXIT
		ENDIF
	ENDDO && End of loops : 1 loop = all that is supposed to happen in synchrony
	thisform.SetAll('ForeColor',pnZwart,'CBD')
	thisform.CBD1.Caption="Run"
	IF nSteps=>100000
		thisform.CBD2.FontSize=7
		thisform.CBD2.Caption="FAILED (get the cursor over here to see the tooltiptext)"
		thisform.CBD2.ToolTipText="FAILED RUN"+pcLF+"LTP to weak in comparison to LTD - or - "+;
			"the repetition has to be increased to avoid trailing behind and falling off of CFs when random activation is too asymmetric."
	ELSE
		thisform.CBD2.Caption="RUN COMPLETED in "+LTRIM(STR(nSteps))+" steps"
	ENDIF
	SET COMPATIBLE ON
	thisform.ENABLECTRLS(.T.)
	thisform.CBD3.Enabled=.F.
	IF plDemo
		thisform.CBLU1.Caption="Red"
	ENDIF
	RETURN
	
	PROCEDURE SLEEP(nDur,	nSecs)
	nSecs=SECONDS()
	DO WHILE SECONDS()-nDur<nSecs
	ENDDO
	RETURN
	
	PROCEDURE PICKGROUPMEMBERS(nLen,	nX,cX,cGroup)
	IF NOT plClustered && Random
		cX=''
		cGroup=pcClF
		FOR nX=1 TO nLen
			cX=cX+SUBSTR(cGroup,RAND()*LEN(cGroup)+1,1)
			cGroup=STUFF(cGroup,AT(RIGHT(cX,1),cGroup),1,'')
		ENDFOR
	ENDIF
	IF plClustered
		cX=LEFT(pcClF_NxtG,nLen)
		pcClF_NxtG=SUBSTR(pcClF_NxtG,nLen+1)
		IF LEN(pcClF_NxtG)<nLen
			pcClF_NxtG=''
		ENDIF
	ENDIF
	RETURN(cX)
	
	PROCEDURE ABORT(nY,	cY,nMember,nPuCPos)
	cY=LTRIM(STR(nY))
	SET COMPATIBLE ON
	thisform.ENABLECTRLS(.T.)
	thisform.CBD3.ForeColor=pnZwart
	thisform.Cls
	FOR nMember=1 TO 10
		nPuCPos=AT(LTRIM(STR(nMember-1)),pcPuC) && De positie vh nMemberste lid in pcPuC
		&& om de lijndikte op te halen die hoort bij het nMemberste lid van pcPuC
		thisform.ForeColor=pnZwart
		FOR nY=1 TO 10
			thisform.DrawWidth=INT(SSP(nPuCPos,nY)+SSD(nPuCPos,nY)) && We tekenen de lijn in 't zwart met de nieuwe dikte
			thisform.Line(pnHPosPuC,pnVOffSet+pnDist*nPuCPos,pnHPosNuC,pnVOffSet+pnDist*nY)
		ENDFOR
		thisform.FIBERS(nMember,0,(pnGroen),(pnGeel),(pnBlauw)) && Fibers terug in oorspronkelijke kleur
	ENDFOR
	thisform.CBR&cY..Click
	thisform.CBD1.Caption="Run"
	IF plDemo
		thisform.CBLU1.Caption="Red"
	ENDIF
	RETURN

	PROCEDURE PAUSE12(nNuCID,nY)
	IF thisform.CBLD1.ForeColor=pnRood
		thisform.PAUSE(1,nNuCID)
	ENDIF
	IF thisform.CBLD2.ForeColor=pnRood
		IF nY=10
			thisform.PAUSE(2,nNuCID)
		ENDIF
	ENDIF
	RETURN

	PROCEDURE PAUSE34(nMember,nClF_ActGLen,lGroupChange)
	IF thisform.CBLD3.ForeColor=pnRood
		IF nMember=nClF_ActGLen
			thisform.PAUSE(3)
		ENDIF
	ENDIF
	IF thisform.CBLD4.ForeColor=pnRood AND lGroupChange
		IF nMember=nClF_ActGLen
			thisform.PAUSE(4)
			lGroupChange=.F.
		ENDIF
	ENDIF
	RETURN(lGroupChange)

	PROCEDURE PAUSE(nStep,nX,	cX)
	thisform.CBLD2.Caption="Single PuC"+IIF(EMPTY(nX),'',pcLF+LTRIM(STR(nX)))
	thisform.CBLD3.Caption="PuC group"+pcLF+pcClF_ActG1
	thisform.CBLD4.Caption="PuC group size"+pcLF+LTRIM(STR(OCCURS(',',pcClF_ActG1)+1))
	IF nStep=0
		RETURN
	ENDIF
	IF EMPTY(nX)
		nX=VAL(SUBSTR(pcClF_ActG1,RAT(',',pcClF_ActG1)+1))
	ENDIF
	cX=LTRIM(STR(AT(LTRIM(STR(nX-1)),pcPuC)))
	thisform.CBR&cX..Click
	cStep=LTRIM(STR(nStep))
	DO WHILE thisform.CBLD&cStep..ForeColor=pnRood
		thisform.CBD2.Caption="Press any key to continue "+pcLIM
		IF plAbort OR INKEY()>0
			EXIT
		ENDIF
		DOEVENTS
	ENDDO
	thisform.CBD2.Caption=''
	IF plAbort
		thisform.CBD2.Caption="Execution aborted "+pcLIM
	ENDIF
	RETURN

	PROCEDURE SLOW(nDW,	nT)
	IF thisform.CBLU2.Caption="Slow"
		IF nDW#thisform.DrawWidth
			FOR nT=1 TO 1000000
				DOEVENTS
			ENDFOR
		ENDIF
	ENDIF
	RETURN

	PROCEDURE CFRETRACT(nLen,	nX,cCF,nC,nY,nR,cCon)
	thisform.SS.Caption="Used PuC-groups"+pcLF+"for each CF"
	FOR nX=1 TO 10
		cCF=LEFT(NUCPUC(11),1)
		NUCPUC(11)=SUBSTR(NUCPUC(11),2)
		NUCPUC(nX)=CHRTRAN(NUCPUC(nX),cCF,'')
		thisform.SS.Caption=thisform.SS.Caption+pcLF+"CF "+LTRIM(STR(nX))+' > '+NUCPUC(nX)
	ENDFOR		
	NUCPUC(11)=SUBSTR(NUCPUC(11),2)
	RETURN
	
	PROCEDURE ENABLECTRLS(lEnable)
	thisform.SetAll("Enabled",lEnable,"CBU")
	thisform.SetAll("Enabled",lEnable,"SP")
	thisform.SetAll("Enabled",lEnable,"RC")
	thisform.SetAll("Enabled",lEnable,"SPLB")
	thisform.SPLB5.Enabled=plClustered
	thisform.SP5.Enabled=plClustered
	RETURN
	
	PROCEDURE SCRAMBLE(nNP,	nP,nX,cX)
	=RAND(-1)
	IF nNP=0
		STORE '' TO pcClF,pcNuC,pcPuC
		FOR nX=1 TO 10
			NUCPUC(nX)=thisform.RSTRING("1234567890",1)
			pcClF=pcClF+SUBSTR(CNP(nX),1,1)
			pcNuC=pcNuC+SUBSTR(CNP(nX),2,1)
			pcPuC=pcPuC+SUBSTR(CNP(nX),3,1)
		ENDFOR
		NUCPUC(11)=REPLICATE(thisform.RSTRING("1234567890",1),11)
		RETURN
	ENDIF

	cX=''
	nP=ABS(nNP)
	FOR nX=1 TO 10
		cX=cX+RIGHT(CNP(nX),nP)
	ENDFOR
	DO CASE
	CASE nNP>0
		cX=thisform.RSTRING(cX,nP)
	CASE nNP<0
		cX=thisform.RASORT(cX,nP)
	ENDCASE
	STORE '' TO pcClF,pcNuC,pcPuC
	FOR nX=1 TO 10
		CNP(nX)=LEFT(CNP(nX),IIF(nP=1,2,1))+LEFT(cX,nP)
		cX=SUBSTR(cX,nP+1)
		pcClF=pcClF+LEFT(CNP(nX),1)
		pcNuC=pcNuC+SUBSTR(CNP(nX),2,1)
		pcPuC=pcPuC+RIGHT(CNP(nX),1)
	ENDFOR
	RETURN
	
	PROCEDURE RSTRING(cPreScramble,nP,	cPostScramble,nX,nAT,cX)
	cPostScramble=''
	FOR nX=1 TO LEN(cPreScramble) STEP nP
		nAT=INT(RAND()*LEN(cPreScramble)/nP)*nP+1
		cX=SUBSTR(cPreScramble,nAT,nP)
		cPostScramble=cPostScramble+cX
		cPreScramble=STUFF(cPreScramble,nAT,nP,'')
	ENDFOR
	RETURN(cPostScramble)
	
	PROCEDURE RASORT(cPreScramble,nP,	cPostScramble,nX)
	DIMENSION RAS[10]
	FOR nX=1 TO 10
		RAS(nX)=LEFT(cPreScramble,nP)
		cPreScramble=SUBSTR(cPreScramble,nP+1)
	ENDFOR
	IF nP=2
		ASORT(RAS)
	ELSE
		FOR nX=1 TO 10
			RAS(nX)=SUBSTR(CNP(nX),2,1)
		ENDFOR
	ENDIF
	cPostScramble=''
	FOR nX=1 TO 10
		cPostScramble=cPostScramble+RAS(nX)
	ENDFOR
	RETURN(cPostScramble)

	PROCEDURE SHOWTXT(cZ,nX,cX,cLTP,cLTD,cLW,nSum,nY)
	cZ=pcLF+"          "
	FOR nX=1 TO 10
		cX=LTRIM(STR(nX))
		cZ=cZ+" PuC"+cX+"  "
	ENDFOR
	cZ=cZ+"SUM    FSUM"+pcLF
	FOR nX=1 TO 10
		cX=LTRIM(STR(nX))
		cLTP='LTP NuC'+cX
		cLTD='LTD NuC'+cX
		cLW="LWidth "+cX
		nSum=0
		FOR nY=1 TO 10
			cLTP=cLTP+STR(SSP(nX,nY),7,2)
			cLTD=cLTD+STR(SSD(nX,nY),7,2)
			cLW=cLW+STR(SSP(nX,nY)+SSD(nX,nY),7,2)
			nSum=nSum+SSP(nX,nY)+SSD(nX,nY)
		ENDFOR
		cZ=cZ+' '+cLTP+pcLF+' '+cLTD+pcLF+' '+cLW+STR(nSum,7,2)+STR(SUMSSP(nX)+SUMSSD(nX),7,2)+pcLF+pcLF
	ENDFOR
	thisform.TXT.Value=cZ
	RETURN

ENDDEFINE

DEFINE CLASS CBU AS COMMANDBUTTON
	FontBold		= .T.
	Top				= 5
	Height			= 20
	Visible			= .T.
	FontSize		= 8
	Alignment		= 2
	BorderStyle		= 1
	TabStop			= .F.
	
	PROCEDURE Init(nN,nX,nW,cTTT,cT)
	nX=VAL(RIGHT(this.Name,1))
	nW=pnW/2
	this.Width=nW/(nN-1)
	this.Left=(nX-1)*this.Width
	this.Caption=STREXTRACT(",CFs (+ cols) not scrambled,CF hand over : one to one,Group size at start = 1,PuC axons not scrambled,,",',',',',nX)
	this.BackColor=thisform.BackColor
	IF nX=5
		this.Left=-1000
	ENDIF
	cT="|Toggle switch :"+pcLF
	cTTT=cT+"for CF scrambling."+cT+"to choose between the following starting conditions :"+pcLF+;
		"Groups of CFs each activating their only target PuC ('one-to-one') - or -"+pcLF+;
		"Each CF capable of activating all ten PuCs ('one-to-many', the early development situation)."+pcLF+;
		"This last setting also automatically sets the next setting to 'Group size at start=10'." 
	cTTT=cTTT+cT+"Setting the group size to one is just for use with the initial demo showing the 'partnership' formation,"+pcLF+;
				 "Setting the group size to ten is for the synchronous group activations."+pcLF+;
				 "Each setting also resets the preprogrammed choices for LTP and LTD."
	cTTT=cTTT+cT+"for PuC axon scrambling.|"
	this.ToolTipText=STREXTRACT(cTTT,'|','|',nX)
	RETURN
	
	PROCEDURE Click(cCap,cT)
	cCap=this.Caption
	plRun=.F.
	DO CASE
	CASE "CFs"$cCap
		this.Caption=IIF("not"$cCap,STRTRAN(cCap,"not ",''),STRTRAN(cCap,"scrambled","not scrambled"))
		thisform.SCRAMBLE(IIF("not"$this.Caption,-2,2))
		thisform.Cls
		thisform.DORUN(1,pnGroupSize)
	CASE "hand"$cCap
		cT=LEFT(cCap,AT("to",cCap)+2)
		this.Caption=IIF("many"$cCap,cT+"one",cT+"many")
		pnGroupSize=10
		IF "many"$this.Caption AND NOT "10"$thisform.CBU3.Caption
			thisform.CBU3.Click && Group size op 10 zetten
		ENDIF
		IF "many"$this.Caption AND NOT plClustered
			plClustered=.T.
		ELSE
			plClustered=.F.
		ENDIF
		thisform.SPLB5.Enabled=plClustered
		thisform.SP5.Enabled=plClustered
	CASE "size"$cCap
		cT=LEFT(cCap,AT("1",cCap))
		this.Caption=IIF("10"$cCap,cT,cT+"0")
		pnGroupSize=IIF("10"$this.Caption,10,1) && Group size
		thisform.SP1.Value=IIF("10"$this.Caption,5.0,.5) && LTP threshold
		thisform.SP2.Value=IIF("10"$this.Caption,1.0,.5) && LTP step
		thisform.SP3.Value=IIF("10"$this.Caption,1.1,1.1) && LTD threshold
		thisform.SP4.Value=IIF("10"$this.Caption,.1,.1) && LTD step
		IF NOT "10"$this.Caption AND "many"$thisform.CBU2.Caption
			thisform.CBU2.Click
		ENDIF
		thisform.SPLB3.Enabled="10"$this.Caption
		thisform.SP3.Enabled="10"$this.Caption
		thisform.SPLB4.Enabled="10"$this.Caption
		thisform.SP4.Enabled="10"$this.Caption
	CASE "PuC"$cCap
		this.Caption=IIF("not"$cCap,STRTRAN(cCap,"not ",''),STRTRAN(cCap,"scrambled","not scrambled"))
		thisform.SCRAMBLE(IIF("not"$this.Caption,-1,1))
		thisform.Cls
		thisform.DORUN(1,pnGroupSize)
	ENDCASE
	thisform.CBU5.SetFocus
	RETURN
	
ENDDEFINE
	
DEFINE CLASS CBLU AS LABEL
	FontBold		= .T.
	Height			= 20
	Width			= 100
	Visible			= .T.
	FontSize		= 8
	Alignment		= 2
	BorderStyle		= 1
	WordWrap		= .T.
	
	PROCEDURE Init(nX,cTTT)
	nX=VAL(RIGHT(this.Name,1))
	this.Top=210+(nX-1)*20
	this.Caption=STREXTRACT(",Red,Fast,",',',',',nX)
	cTTT="|Toggle switch : 'Red' shows PuC terminals in red when activated, 'No red' doesn't (making the display quieter)."
	cTTT=cTTT+"|Toggle switch : 'Fast' executes the program at top speed, 'Slow' inserts a small pause when a line width changes. "+;
								"You can however use the different interrupt options of the buttons below.|"
	this.ToolTipText=STREXTRACT(cTTT,'|','|',nX)
	this.ZOrder(1)
	RETURN
	
	PROCEDURE Click(nX)
	nX=VAL(RIGHT(this.Name,1))
	DO CASE
	CASE nX=1
		IF this.Caption="Red"
			this.Caption="No red"
		ELSE
			this.Caption="Red"
		ENDIF
	CASE nX=2
		IF this.Caption="Fast"
			this.Caption="Slow"
		ELSE
			this.Caption="Fast"
		ENDIF
	ENDCASE
	RETURN
	
ENDDEFINE

DEFINE CLASS CBLD AS LABEL
	FontBold		= .T.
	Height			= 28
	Width			= 100
	Visible			= .T.
	FontSize		= 7
	Alignment		= 2
	BorderStyle		= 1
	WordWrap		= .T.
	
	PROCEDURE Init(nX,cTTT)
	nX=VAL(RIGHT(this.Name,1))
	this.Top=pnH-(6-nX)*28
	this.Caption=STREXTRACT(",Single PuC axon branch,Single PuC,PuC group,PuC group size,Clear interrupts,",',',',',nX)
	cTTT="|Click to interrupt program execution after each PuC terminal branch firing (the elementary program step)."
	cTTT=cTTT+"|Click to interrupt program execution after each PuC having fired all it's terminal branches."
	cTTT=cTTT+"|Click to interrupt program execution after the processing of each PuC group "+;
			  "(which is the equivalent of what is considered to have happened synchronously in vivo)."
	cTTT=cTTT+"|Click to interrupt program execution when the conditions are ready to decrement the used PuC group size."
	cTTT=cTTT+"|Click to clear your above interrupt setting, and to continue the program without interruption (when it is executing).|"
	this.ToolTipText=STREXTRACT(cTTT,'|','|',nX)
	this.ZOrder(1)
	RETURN
	
	PROCEDURE Click
	thisform.SetAll('ForeColor',pnZwart,'CBLD')
	IF NOT "Clear"$this.Caption
		this.ForeColor=pnRood
	ENDIF
	RETURN
	
ENDDEFINE

DEFINE CLASS CBD AS LABEL 
	FontBold		= .T.
	Top				= pnVOffSet+pnDist*10+55
	Height			= 20
	Visible			= .T.
	FontSize		= 8
	Alignment		= 2
	BorderStyle		= 1

	PROCEDURE Init(nX,nW,cTTT)
	nX=VAL(RIGHT(this.Name,1))
	nW=(pnHPosPuc+42)-(pnHPosNuC-42)
	this.Width=nW/5*IIF(nX=2,3,1)+2
	this.Left=pnHPosNuC-42+ICASE(nX=1,0,nX=2,1,nX=3,4)*nW/5
	this.Caption=STREXTRACT(",Run,,Abort,",',',',',nX)
	this.BackColor=thisform.BackColor
	cTTT="|Starts execution|For status display only|Aborts execution|"
	this.ToolTipText=STREXTRACT(cTTT,'|','|',nX)
	RETURN
	
	PROCEDURE MouseDown
	LPARAMETERS nButton, nShift, nXCoord, nYCoord,	cCap
	STORE .F. TO plRun,plAbort
	thisform.SetAll('ForeColor',pnZwart,'CBD')
	cCap=this.Caption
	DO CASE
	CASE cCap="Run"
		thisform.CBD2.Caption=''
		this.ForeColor=pnGeel
		thisform.CBU1.Click
		thisform.CBU1.Click
		thisform.CBU4.Click
		thisform.CBU4.Click
		plRun=.T.
		thisform.Cls
		thisform.DORUN((pnGroupSize),(pnGroupSize))
	CASE cCap="Abort"
		thisform.CBD2.Caption="Execution aborted"
		thisform.CBD2.Refresh
		plAbort=.T.
	ENDCASE
	RETURN
	
ENDDEFINE

DEFINE CLASS CBR AS LABEL
	Top				= pnVOffSet+pnDist*10+55
	Height			= pnRad
	Width			= pnRad
	Visible			= .T.
	FontSize		= 6
	Alignment		= 2
	FontBold		= .T.

	PROCEDURE Init(nX)
	nX=VAL(SUBSTR(this.Name,4))
	this.Top=pnVOffSet+pnDist*nX+2
	this.Left=pnHPosPuC+23
	this.Caption='?'
	this.ToolTipText="Click to see (in the left side table) the actual SSs of all terminals of this PuC."
	RETURN
	
	PROCEDURE Click(nPos,nPuCID,nSum,cX,nY,nDW)
	nPos=VAL(SUBSTR(this.Name,4))
	nPuCID=VAL(SUBSTR(pcPuC,nPos,1))+1
&&	nSum=0
	cX=''
	FOR nY=1 TO 10
		nDW=SSP(nPos,nY)+SSD(nPos,nY)
		cX=cX+"br "+STR(nY,2)+" = "+STR(nDW,5,2)+pcLF
&&		nSum=nSum+nDW
	ENDFOR
	thisform.SS.Caption=pcLF+"PuC "+LTRIM(STR(nPuCID))+" SSs"+pcLF+cX &&+"-------------"+pcLF+"  Sum = "+STR(nSum,5,2)
	RETURN
	
ENDDEFINE

DEFINE CLASS SSLB AS LABEL
	FontBold		= .T.
	FontName		= "Courier New"
	FontSize		= 8
	Width			= 50
	Height			= 200
	Top				= 300
	Alignment		= 2
	
ENDDEFINE

DEFINE CLASS SPLB AS COMMANDBUTTON
	FontBold		= .T.
	Height			= 30
	Width			= 50
	Visible			= .T.
	FontSize		= 7
	Alignment		= 2
	WordWrap		= .T.

	PROCEDURE Init(nN,nX,nW,cTTT)
	nX=VAL(RIGHT(this.Name,1))
	this.Top=60+(nX-1)*30
	this.Caption=STREXTRACT(",LTP threshold,LTP step,LTD threshold,LTD step,Repeating factor,",',',',',nX)
	cTTT="|When the sum of SSs of FIRING PuC terminals (see figures underneath the NuCs while executing) converging on an ACTIVATED NuC (red circle)"+;
		" exceeds this threshold, LTP occurs (at these firing PuC-NuC synapses only) - and the NuC will show in yellow."
	cTTT=cTTT+"|Sets the step by which LTP increases the SSs."
	cTTT=cTTT+"|When the sum of SSs of FIRING PuC terminals (see figures underneath the NuCs while executing) converging on a NON-ACTIVATED NuC (NO red circle)"+;
		" exceeds this threshold, LTD occurs (at these firing synapses only) - and in this case the NuC will show in dark blue, "+;
		"otherwise it will show in it's 'basic' green (no LTD nor LTP occurring). LTD not applicable when group size=1."
	cTTT=cTTT+"|Sets the step by which LTD decreases the SSs. LTD not applicable when group size=1."
	cTTT=cTTT+"|When one CF activates many PuCs :"+pcLF+;
		 "Repeated activation of the same PuC-group before the group size is allowed to decrement"+;
		 " will help to avoid LTP lagging behind and stopping or even reverting"+;
		 " when specific CFs have not been activated enough due to asymmetric random activation.|"
	this.ToolTipText=STREXTRACT(cTTT,'|','|',nX)
	IF nX=5
		this.Enabled=.F.
	ENDIF	
	this.ZOrder(1)
	RETURN
	
ENDDEFINE

DEFINE CLASS SP AS SPINNER
	FontBold		= .T.
	Height			= 30
	Width			= 50
	Visible			= .T.
	FontSize		= 7
	Left			= 50
	SpinnerLowValue	= 0.0
	Increment		= 0.1
	Value			= 0.1

	PROCEDURE Init(nN,nX,nW)
	nX=VAL(RIGHT(this.Name,1))
	this.Top=60+(nX-1)*30
	this.ZOrder(1)
	DO CASE
	CASE nX=3
		this.SpinnerLowValue=1.1
	CASE nX=5
		this.SpinnerLowValue=1
		this.SpinnerHighValue=30
		this.Increment=1
		this.Value=5
		this.Enabled=.F.
	ENDCASE
	RETURN
	
ENDDEFINE

PROCEDURE INITCOLOR
pnZwart=				RGB(0,0,0)
pnLichtGrijs=			RGB(192,192,192)
pnGrijs=				RGB(128,128,128)
pnDonkerGrijs=			RGB(32,32,32)
pnWit=					RGB(255,255,255)

pnLichtRood=			RGB(255,128,128)
pnRood=					RGB(255,0,0)
pnDonkerRood=			RGB(128,0,0)
pnLichtGroen=			RGB(128,255,128)
pnGroen=				RGB(0,255,0)
pnDonkerGroen=			RGB(0,128,0)

pnBlauw=				RGB(0,0,255)
pnDonkerBlauw=			RGB(0,0,128)
pnGeel=					RGB(255,255,0)
pnLichtGeel=			RGB(255,255,128)
pnHalfDonkerGeel=		RGB(255,128,0)
pnDonkerGeel=			RGB(128,128,0)

pnCyaan=				RGB(0,255,255)
pnLichtCyaan=			RGB(128,255,255)
pnHalfDonkerCyaan=		RGB(0,128,255)
pnDonkerCyaan=			RGB(0,128,128)
pnMagenta=				RGB(255,0,255)
pnLichtMagenta=			RGB(255,128,255)

RETURN

	PROCEDURE DING
   SET BELL TO LEFT(pcDIR,2)+'\WINDOWS\MEDIA\WINDOWS DING.WAV',1 && !!!
   ?? CHR(7)
   SET BELL TO
   RETURN
   
	PROCEDURE CHORD
   SET BELL TO LEFT(pcDIR,2)+'\WINDOWS\MEDIA\CHORD.WAV',1 && !!!
   ?? CHR(7),CHR(7)
   SET BELL TO
   RETURN
   
