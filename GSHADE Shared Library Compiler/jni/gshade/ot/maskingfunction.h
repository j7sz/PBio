/*
 * MaskingFunction.h
 *
 *  Created on: May 13, 2013
 *      Author: mzohner
 */

#ifndef MASKINGFUNCTION_H_
#define MASKINGFUNCTION_H_

#include "../util/cbitvector.h"
#include "../util/typedefs.h"

class MaskingFunction
{

public:
	MaskingFunction(){};
	~MaskingFunction(){};

	virtual void	Mask(int progress, int len, CBitVector* values, CBitVector* snd_buf, BYTE protocol)  = 0;
	virtual void 	UnMask(int progress, int len, CBitVector& choices, CBitVector& output, CBitVector& rcv_buf, BYTE version) = 0;
	virtual void  expandMask(CBitVector& out, BYTE* sbp, int offset, int processedOTs, int bitlength) = 0;


protected:


};


#endif /* MASKINGFUNCTION_H_ */
