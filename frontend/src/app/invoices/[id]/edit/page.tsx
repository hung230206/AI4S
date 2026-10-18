import {InvoiceForm} from "@/components/invoice-form";
export default async function EditInvoice({params}: {params: Promise<{id: string}>}) {return <InvoiceForm invoiceId={(await params).id}/>;}
