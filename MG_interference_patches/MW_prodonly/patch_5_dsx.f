395,401d394
<       DO I = 1, NCOLOR
<         ZTEMP = (0.D0,0.D0)
<         DO J = 1, NCOLOR
<           ZTEMP = ZTEMP + CF(J,I)*JAMP(J)
<         ENDDO
<         MATRIX5 = MATRIX5+ZTEMP*DCONJG(JAMP(I))/DENOM(I)
<       ENDDO
