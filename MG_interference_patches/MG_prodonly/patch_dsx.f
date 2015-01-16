533,545c533,545
<       DO M = 1, NAMPSO
<         DO I = 1, NCOLOR
<           ZTEMP = (0.D0,0.D0)
<           DO J = 1, NCOLOR
<             ZTEMP = ZTEMP + CF(J,I)*JAMP(J,M)
<           ENDDO
<           DO N = 1, NAMPSO
<             IF (CHOSEN_SO_CONFIGS(SQSOINDEX1(M,N))) THEN
<               MATRIX1 = MATRIX1 + ZTEMP*DCONJG(JAMP(I,N))/DENOM(I)
<             ENDIF
<           ENDDO
<         ENDDO
<       ENDDO
---
> C     DO M = 1, NAMPSO
> C       DO I = 1, NCOLOR
> C         ZTEMP = (0.D0,0.D0)
> C         DO J = 1, NCOLOR
> C           ZTEMP = ZTEMP + CF(J,I)*JAMP(J,M)
> C         ENDDO
> C         DO N = 1, NAMPSO
> C           IF (CHOSEN_SO_CONFIGS(SQSOINDEX1(M,N))) THEN
> C             MATRIX1 = MATRIX1 + ZTEMP*DCONJG(JAMP(I,N))/DENOM(I)
> C           ENDIF
> C         ENDDO
> C       ENDDO
> C     ENDDO
