357c357
<       INTEGER I,J
---
>       INTEGER I,J,M,N
360c360
<       COMPLEX*16 AMP(NGRAPHS), JAMP(NCOLOR)
---
>       COMPLEX*16 AMP(NGRAPHS), JAMP(NCOLOR,2)
424,427c424,429
<       JAMP(1)=+AMP(1)-1D0/6D0*AMP(2)-1D0/6D0*AMP(3)-1D0/6D0*AMP(4)
<      $ +AMP(5)+AMP(6)-1D0/6D0*AMP(7)-1D0/6D0*AMP(8)+AMP(9)+AMP(10)
<      $ +AMP(11)+AMP(12)
<       JAMP(2)=+1D0/2D0*(+AMP(2)+AMP(3)+AMP(4)+AMP(7)+AMP(8))
---
>       JAMP(1,1)=+AMP(6)-1D0/6D0*AMP(8)+AMP(10)+AMP(12)
>       JAMP(1,2)=+AMP(1)-1D0/6D0*AMP(2)-1D0/6D0*AMP(3)-1D0/6D0*AMP(4)
>      $ +AMP(5)-1D0/6D0*AMP(7)+AMP(9)+AMP(11)
>       
>       JAMP(2,1)=+1D0/2D0*(AMP(8))
>       JAMP(2,2)=+1D0/2D0*(+AMP(2)+AMP(3)+AMP(4)+AMP(7))
430,433c432,442
<       DO I = 1, NCOLOR
<         ZTEMP = (0.D0,0.D0)
<         DO J = 1, NCOLOR
<           ZTEMP = ZTEMP + CF(J,I)*JAMP(J)
---
>       DO M = 1, 2 
>         DO I = 1, NCOLOR
>           ZTEMP = (0.D0,0.D0)
>           DO J = 1, NCOLOR
>             ZTEMP = ZTEMP + CF(J,I)*JAMP(J,M)
>           ENDDO
>           DO N = 1, 2
>             IF ((M+N).EQ.3) THEN
>               MATRIX3=MATRIX3+ZTEMP*DCONJG(JAMP(I,N))/DENOM(I)
>             ENDIF
>           ENDDO
435d443
<         MATRIX3 = MATRIX3+ZTEMP*DCONJG(JAMP(I))/DENOM(I)
