490c490
<       COMPLEX*16 AMP(NGRAPHS), JAMP(NCOLOR,NAMPSO)
---
>       COMPLEX*16 AMP(NGRAPHS), JAMP(NCOLOR,2)
562,566c562,569
<       JAMP(1,1)=-IMAG1*AMP(1)-IMAG1*AMP(3)-IMAG1*AMP(4)-IMAG1*AMP(5)
<      $ +AMP(6)+AMP(7)+AMP(8)
<       JAMP(2,1)=+IMAG1*AMP(1)+IMAG1*AMP(3)+IMAG1*AMP(4)+IMAG1*AMP(5)
<      $ +AMP(9)+AMP(10)+AMP(11)
<       JAMP(3,1)=+2D0*(+AMP(2))
---
>       JAMP(1,1)=-IMAG1*AMP(5)+AMP(8)
>       JAMP(1,2)=-IMAG1*AMP(1)-IMAG1*AMP(3)-IMAG1*AMP(4)+AMP(6)+AMP(7)
> 
>       JAMP(2,1)=+IMAG1*AMP(5)+AMP(11)
>       JAMP(2,2)=+IMAG1*AMP(1)+IMAG1*AMP(3)+IMAG1*AMP(4)+AMP(9)+AMP(10)
> 
>       JAMP(3,1)=(0.D0,0.D0)
>       JAMP(3,2)=+2D0*(+AMP(2))
569c572
<       DO M = 1, NAMPSO
---
>       DO M = 1, 2 
575,577c578,580
<           DO N = 1, NAMPSO
<             IF (CHOSEN_SO_CONFIGS(SQSOINDEX1(M,N))) THEN
<               MATRIX1 = MATRIX1 + ZTEMP*DCONJG(JAMP(I,N))/DENOM(I)
---
>           DO N = 1, 2
>             IF ((M+N).EQ.3) THEN
>               MATRIX1=MATRIX1+ZTEMP*DCONJG(JAMP(I,N))/DENOM(I)
591,594c594,597
<         DO M = 1, NAMPSO
<           DO N = 1, NAMPSO
<             IF (CHOSEN_SO_CONFIGS(SQSOINDEX1(M,N))) THEN
<               JAMP2(I)=JAMP2(I)+JAMP(I,M)*DCONJG(JAMP(I,N))
---
>         DO M = 1, 2
>           DO N = 1, 2
>             IF ((M+N).EQ.3) THEN
>               JAMP2(I)=JAMP2(I)+ABS(JAMP(I,M)*DCONJG(JAMP(I,N)))
