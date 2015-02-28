357c357
<       INTEGER I,J
---
>       INTEGER I,J,M,N
360c360
<       COMPLEX*16 AMP(NGRAPHS), JAMP(NCOLOR)
---
>       COMPLEX*16 AMP(NGRAPHS), JAMP(NCOLOR,2)
424,428c424,431
<       JAMP(1)=-IMAG1*AMP(1)-IMAG1*AMP(3)-IMAG1*AMP(4)-IMAG1*AMP(5)
<      $ +AMP(6)+AMP(7)+AMP(8)
<       JAMP(2)=+IMAG1*AMP(1)+IMAG1*AMP(3)+IMAG1*AMP(4)+IMAG1*AMP(5)
<      $ +AMP(9)+AMP(10)+AMP(11)
<       JAMP(3)=+2D0*(+AMP(2))
---
>       JAMP(1,1)=-IMAG1*AMP(5)+AMP(8)
>       JAMP(1,2)=-IMAG1*AMP(1)-IMAG1*AMP(3)-IMAG1*AMP(4)+AMP(6)+AMP(7)
> 
>       JAMP(2,1)=+IMAG1*AMP(5)+AMP(11)
>       JAMP(2,2)=+IMAG1*AMP(1)+IMAG1*AMP(3)+IMAG1*AMP(4)+AMP(9)+AMP(10)
> 
>       JAMP(3,1)=(0.D0,0.D0)
>       JAMP(3,2)=+2D0*(+AMP(2))
431,434c434,444
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
>               MATRIX1=MATRIX1+ZTEMP*DCONJG(JAMP(I,N))/DENOM(I)
>             ENDIF
>           ENDDO
436d445
<         MATRIX1 = MATRIX1+ZTEMP*DCONJG(JAMP(I))/DENOM(I)
